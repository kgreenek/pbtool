import argparse
import os
import re
import subprocess

def main():
    arg_parser = argparse.ArgumentParser(description="Generate bazel BUILD file for protos in a "
                                         "directory")
    arg_parser.add_argument("path", type=str, help="The path of the proto files")
#    arg_parser.add_argument("--workspace", type=str, help="The workspace directory. All "
#                            "subdirectories in the workspace will be searched for dependencies. "
#                            "Useful if you are generating build files for protos in a bazel "
#                            "workspace")
    arg_parser.add_argument("--cc", action="store_true", help="Also generate cc_proto rules")
    arg_parser.add_argument("--src_prefix", type=str, help="A prefix that is appended to the path "
                            "of each src in srcs")
    args = arg_parser.parse_args()

    src_prefix = args.src_prefix if args.src_prefix != None else ""
    if not src_prefix.endswith("/") and src_prefix != "":
        src_prefix = src_prefix + "/"

    try:
        os.remove("BUILD")
    except OSError:
        pass

    os.chdir(args.path)

    bazel_workspace = ""
    bazel_workspace_cmd_result = subprocess.run(["bazel", "info", "workspace"],
                                                stdout=subprocess.PIPE)
    if bazel_workspace_cmd_result.returncode == 0 and bazel_workspace_cmd_result.stdout != "":
        # The stdout value from the command looks like this: b/'/path/to/workspace'\n
        # We need to strip off the "b/'" prefix and the "'\n" suffix to get the path.
        bazel_workspace = str(bazel_workspace_cmd_result.stdout)[2:-3]
        print("Using bazel workspace: " + bazel_workspace)
    else:
        print("No bazel workspace")

    proto_file_paths = []
    for (dir_path, dir_names, file_names) in os.walk(args.path):
        dir_path = "" if dir_path == "." else dir_path
        proto_file_paths.extend([dir_path + f for f in file_names if f.endswith(".proto")])
        break
    proto_file_paths = sorted(proto_file_paths)

    if len(proto_file_paths) == 0:
        print("No proto files found in path: " + args.path)
        return

    with open("BUILD", "w") as build_file:
        first = True
        for proto_file_path in proto_file_paths:
            proto_dir_name, proto_file_name = os.path.split(proto_file_path)
            proto_target = proto_file_name.replace(".proto", "_proto")
            deps = []
            with open(proto_file_path, "r") as proto_file:
                for line in proto_file:
                    import_value = re.findall('^\s*import\s+"([^"]+)"\s*;\s*$', line)
                    if len(import_value) == 1:
                        dep_dir_name, dep_file_name = os.path.split(import_value[0])
                        dep_target = ":" + dep_file_name.replace(".proto", "_proto")
                        if dep_dir_name == "" or \
                                os.path.join(bazel_workspace, dep_dir_name) == os.getcwd():
                            if not os.path.isfile(os.path.join(proto_dir_name, dep_file_name)):
                                print("WARNING: Imported file doesn't exist in cwd: " +
                                      import_value[0])
                            deps.append(dep_target)
                        else:
                            if not os.path.isfile(os.path.join(bazel_workspace, import_value[0])):
                                print("WARNING: Imported file doesn't exist in workspace: " +
                                      import_value[0])
                            deps.append("//" + dep_dir_name + dep_target)
            deps = sorted(deps)

            if not first:
                build_file.write("\n")
            proto_library_name = proto_file_name.replace(".proto", "_proto")
            build_file.write("proto_library(\n"
                             "    name = \"" + proto_library_name + "\",\n"
                             "    srcs = [\"" + src_prefix + proto_file_name + "\"],\n")
            if len(deps) == 1:
                build_file.write("    deps = [\"" + deps[0] + "\"],\n")
            elif len(deps) > 1:
                build_file.write("    deps = [\n")
                for dep in deps:
                    build_file.write("        \"" + dep + "\",\n")
                build_file.write("    ],\n")
            build_file.write("    visibility = [\"//visibility:public\"],\n"
                             ")\n")

            if args.cc:
                build_file.write("\ncc_proto_library(\n"
                                 "    name = \"" + proto_file_name.replace(".proto", "_cc_proto") \
                                        + "\",\n"
                                 "    deps = [\":" + proto_library_name + "\"],\n"
                                 "    visibility = [\"//visibility:public\"],\n"
                                 ")\n")

            first = False

    print("BUILD file created at: " + os.path.join(os.getcwd(), "BUILD"))


if __name__ == "__main__":
    main()
