import argparse
import os
import re

def main():
    arg_parser = argparse.ArgumentParser(description="Generate bazel BUILD file for protos in a "
                                         "directory")
    arg_parser.add_argument("path", type=str, help="The path of the proto files")
    arg_parser.add_argument("--src_prefix", type=str, help="A prefix that is appended to the path "
                            "of each src in srcs")
    args = arg_parser.parse_args()

    src_prefix = args.src_prefix if args.src_prefix != None else ""
    src_prefix = src_prefix + "/" if not src_prefix.endswith("/") and src_prefix != "" \
            else src_prefix

    proto_file_paths = []
    for (dir_path, dir_names, file_names) in os.walk(args.path):
        proto_file_paths.extend([dir_path + f for f in file_names if f.endswith(".proto")])
        break
    proto_file_paths = sorted(proto_file_paths)

    if len(proto_file_paths) == 0:
        return

    try:
        os.remove("BUILD")
    except OSError:
        pass

    build_file = open("BUILD", "w")
    for proto_file_path in proto_file_paths:
        proto_dir_name, proto_file_name = os.path.split(proto_file_path)
        deps = []
        with open(proto_file_path, "r") as proto_file:
            for line in proto_file:
                import_value = re.findall('^\s*import\s+"([^"]+)"\s*;\s*$', line)
                if len(import_value) == 1:
                    deps.append(import_value[0].split("/")[-1].replace(".proto", "_proto"))
        deps = sorted(deps)

        build_file.write("\nproto_library(\n"
                         "    name = \"" + proto_file_name.replace(".proto", "_proto") + "\",\n"
                         "    srcs = [\"" + src_prefix + proto_file_name + "\"],\n")
        if len(deps) == 1:
            build_file.write("    deps = [\":" + deps[0] + "\"],\n")
        elif len(deps) > 1:
            build_file.write("    deps = [\n")
            for dep in deps:
                build_file.write("        \":" + dep + "\",\n")
            build_file.write("    ],\n")
        build_file.write(")\n")
    build_file.close()


if __name__ == "__main__":
    main()
