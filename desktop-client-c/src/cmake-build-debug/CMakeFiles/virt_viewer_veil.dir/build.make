# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.14

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:


#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:


# Remove some rules from gmake that .SUFFIXES does not remove.
SUFFIXES =

.SUFFIXES: .hpux_make_needs_suffix_list


# Suppress display of executed commands.
$(VERBOSE).SILENT:


# A target that is always out of date.
cmake_force:

.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /home/ubuntu/CLion-2019.1.4/clion-2019.1.4/bin/cmake/linux/bin/cmake

# The command to remove a file.
RM = /home/ubuntu/CLion-2019.1.4/clion-2019.1.4/bin/cmake/linux/bin/cmake -E remove -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/ubuntu/job/virt-viewer-veil/src

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug

# Include any dependencies generated for this target.
include CMakeFiles/virt_viewer_veil.dir/depend.make

# Include the progress variables for this target.
include CMakeFiles/virt_viewer_veil.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/virt_viewer_veil.dir/flags.make

CMakeFiles/virt_viewer_veil.dir/crashhandler.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/crashhandler.c.o: ../crashhandler.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/virt_viewer_veil.dir/crashhandler.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/crashhandler.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/crashhandler.c

CMakeFiles/virt_viewer_veil.dir/crashhandler.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/crashhandler.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/crashhandler.c > CMakeFiles/virt_viewer_veil.dir/crashhandler.c.i

CMakeFiles/virt_viewer_veil.dir/crashhandler.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/crashhandler.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/crashhandler.c -o CMakeFiles/virt_viewer_veil.dir/crashhandler.c.s

CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.o: ../ovirt-foreign-menu.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Building C object CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/ovirt-foreign-menu.c

CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/ovirt-foreign-menu.c > CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.i

CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/ovirt-foreign-menu.c -o CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.s

CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.o: ../remote-viewer-connect.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_3) "Building C object CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/remote-viewer-connect.c

CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/remote-viewer-connect.c > CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.i

CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/remote-viewer-connect.c -o CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.s

CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.o: ../remote-viewer-iso-list-dialog.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_4) "Building C object CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/remote-viewer-iso-list-dialog.c

CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/remote-viewer-iso-list-dialog.c > CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.i

CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/remote-viewer-iso-list-dialog.c -o CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.s

CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.o: ../remote-viewer-main.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_5) "Building C object CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/remote-viewer-main.c

CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/remote-viewer-main.c > CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.i

CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/remote-viewer-main.c -o CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.s

CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.o: ../remote-viewer.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_6) "Building C object CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/remote-viewer.c

CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/remote-viewer.c > CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.i

CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/remote-viewer.c -o CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.o: ../virt-viewer-app.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_7) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-app.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-app.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-app.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.o: ../virt-viewer-auth.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_8) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-auth.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-auth.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-auth.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.o: ../virt-viewer-display-spice.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_9) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-display-spice.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-display-spice.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-display-spice.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.o: ../virt-viewer-display.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_10) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-display.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-display.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-display.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.o: ../virt-viewer-enums.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_11) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-enums.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-enums.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-enums.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.o: ../virt-viewer-file-transfer-dialog.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_12) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-file-transfer-dialog.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-file-transfer-dialog.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-file-transfer-dialog.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.o: ../virt-viewer-file.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_13) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-file.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-file.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-file.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.o: ../virt-viewer-notebook.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_14) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-notebook.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-notebook.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-notebook.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.o: ../virt-viewer-resources.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_15) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-resources.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-resources.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-resources.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.o: ../virt-viewer-session-spice.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_16) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-session-spice.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-session-spice.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-session-spice.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.o: ../virt-viewer-session.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_17) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-session.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-session.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-session.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.o: ../virt-viewer-timed-revealer.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_18) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-timed-revealer.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-timed-revealer.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-timed-revealer.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.o: ../virt-viewer-util.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_19) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-util.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-util.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-util.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.o: ../virt-viewer-vm-connection.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_20) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-vm-connection.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-vm-connection.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-vm-connection.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.s

CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.o: CMakeFiles/virt_viewer_veil.dir/flags.make
CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.o: ../virt-viewer-window.c
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_21) "Building C object CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.o   -c /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-window.c

CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-window.c > CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.i

CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/ubuntu/job/virt-viewer-veil/src/virt-viewer-window.c -o CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.s

# Object files for target virt_viewer_veil
virt_viewer_veil_OBJECTS = \
"CMakeFiles/virt_viewer_veil.dir/crashhandler.c.o" \
"CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.o" \
"CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.o" \
"CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.o" \
"CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.o" \
"CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.o" \
"CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.o"

# External object files for target virt_viewer_veil
virt_viewer_veil_EXTERNAL_OBJECTS =

virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/crashhandler.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/ovirt-foreign-menu.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/remote-viewer-connect.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/remote-viewer-iso-list-dialog.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/remote-viewer-main.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/remote-viewer.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-app.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-auth.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-display-spice.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-display.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-enums.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-file-transfer-dialog.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-file.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-notebook.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-resources.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-session-spice.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-session.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-timed-revealer.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-util.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-vm-connection.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/virt-viewer-window.c.o
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/build.make
virt_viewer_veil: CMakeFiles/virt_viewer_veil.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles --progress-num=$(CMAKE_PROGRESS_22) "Linking C executable virt_viewer_veil"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/virt_viewer_veil.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/virt_viewer_veil.dir/build: virt_viewer_veil

.PHONY : CMakeFiles/virt_viewer_veil.dir/build

CMakeFiles/virt_viewer_veil.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/virt_viewer_veil.dir/cmake_clean.cmake
.PHONY : CMakeFiles/virt_viewer_veil.dir/clean

CMakeFiles/virt_viewer_veil.dir/depend:
	cd /home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/ubuntu/job/virt-viewer-veil/src /home/ubuntu/job/virt-viewer-veil/src /home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug /home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug /home/ubuntu/job/virt-viewer-veil/src/cmake-build-debug/CMakeFiles/virt_viewer_veil.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/virt_viewer_veil.dir/depend

