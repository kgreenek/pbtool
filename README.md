# pbtool
pbtool.py is a tool for generating BUILD files for a directory of .proto files. It is primarily useful when creating a BUILD file for an external (non-bazelified) dependency that has a large number of protos.


# Usage
```bash
python pbtool.py /path/to/proto/dir
```

pbtool will create a BUILD file in the current directory with proto_library rules for all the proto files in the proto path. 


For example, if you have 2 proto files called example1.proto and example2.proto, where example2.proto imports example1.proto, the generated BUILD file will look something like this:


```python
proto_library(
    name = "example1_proto",
    srcs = ["example1.proto"],
)

proto_library(
    name = "example2_proto",
    srcs = ["example2.proto"],
    deps = [":example1_proto"],
)
```


NOTE: If you have a file called BUILD in the current working directory already, it'll be overwritten.


## src_prefix
For external dependencies, you'll often need to append a path prefix to the files in srcs. For this case, you can use the --src_prefix option. 

```bash
python pbtool.py /path/to/proto/dir --src_prefix relative/path/to/proto/srcs
```

The generated rule in the BUILD file will look something like this:

```python
proto_library(
    name = "example_proto",
    srcs = ["relative/path/to/proto/srcs/example.proto"],
)
```



# Gotchas & Limitations
Bazel 0.4.5 and older had a [bug](https://github.com/bazelbuild/bazel/issues/2916) in the proto_library rule, where proto dependencies were simply broken. The next release after 0.4.5 will include the fix for that bug. So, depending on when you're reading this, you'll likely have to checkout bazel on HEAD and [build it from source](https://bazel.build/versions/master/docs/install-compile-source.html) in order to use the generated BUILD file.


Right now, pbtool doesn't recursively search the proto directory. This means that all protos and their dependencies must be in the same directory. Let me know if that's a feature you want/need!


# Background
The need for the tool came about because I was doing a project using Bazel that has a dependency on the [ignition msgs library](https://bitbucket.org/ignitionrobotics/ign-msgs). That library doesn't support bazel, so I had to create a BUILD file for it. However, that library has 100+ protobufs! Bazel's proto_library rule requires you to explicitly specify the dependency relationships between protos, which means manually browsing through every proto, checking what it imports, and adding the corresponding deps to the rule. It quickly became apparent that creating the BUILD files by hand was going to take a very long time, and making a script to generate the BUILD file was pretty straight-forward. So here we are :)
