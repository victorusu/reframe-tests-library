
# **ReFrame Test Library**

![GitHub license](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/victorusu/reframe-test-library)
![GitHub issues](https://img.shields.io/github/issues/victorusu/reframe-test-library)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/victorusu/reframe-test-library/ci.yml?branch=main)

## **Table of Contents**
- [Overview](#overview)
- [Key Features](#key-features)
- [Library Design](#library-design)
- [Installation & Setup](#installation--setup)
  - [Prerequisites](#prerequisites)
  - [Clone the Repository](#clone-the-repository)
  - [Configuring ReFrame](#configuring-reframe)
- [Usage](#usage)
  - [Running Ready-to-Use Tests](#running-ready-to-use-tests)
  - [Writing Your Own Tests](#writing-your-own-tests)
  - [Starting from the Check Mixins](#starting-from-the-check-mixins)
  - [Starting from the Provided Checks](#starting-from-the-provided-checks)
- [Example Output](#example-output)
- [Contributing](#contributing)
- [License](#license)

---

## **Overview**

This repository provides a structured **library of ReFrame tests** in a reusable format. The goal is to provide a modular approach to test creation and execution, making it easier to define and extend test cases while minimizing redundancy.

Instead of defining complete ReFrame tests from scratch, this library provides **composable test logic** through mixins, allowing users to easily adapt tests to different system environments while keeping the core test logic reusable.

This library enables users to write tests that focus on system-specific configurations while inheriting common execution behaviors.

**What’s system-specific in this context?**
- How to make the software available (e.g., Spack, EasyBuild, Containers, or manual installations)
- The system's partitions
- Number of nodes required
- Number of tasks per node
- Number of CPUs per task

I hope that by leveraging this structure, the library enables a more flexible and maintainable approach to running **ReFrame-based regression tests** across different HPC and computing environments. The library enables easy adaptation to different HPC environments **without modifying the core test logic**

## **Key Features**

- **Reusable Library Format** – Organizes **ReFrame tests** in a structured and modular way.
- **Composability** – Uses `RegressionMixin` to separate test logic from system-specific details.
- **System-Specific Configurations** – Allows customization of nodes, tasks per node, CPUs per task, and software dependencies.
- **Ready-to-Run Tests** – Includes a collection of tests that can be executed with minimal setup.


## **Library Design**

The core concept of this library is to encapsulate the **test execution logic** in a composable format using a mixin-based design (`RegressionMixin`). This allows individual test cases to inherit the common execution behavior while keeping **system-specific configurations separate**. This approach ensures that only essential aspects—such as how the software is made available, the number of nodes, tasks per node, CPUs per task, and other environment-specific parameters—need to be defined explicitly in derived tests.


### **Why Use `RegressionMixin` Instead of `RegressionTest`?**

This choice is driven by **ReFrame**:

- **Multiple inheritance from more than one `RegressionTest` class is not allowed**
- To enable test **composability**, we use **mixins** instead
- ReFrame’s **`RegressionTestMeta` metaclass** allows mixin classes to use powerful ReFrame features, such as:
  - Hooks
  - Parameters
  - Variables

**Reference**: [ReFrame Regression Test API](https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html)

---

### **The Need for Composability**

The **multi-inheritance limitation** in ReFrame prevents composition of different test types. **Mixins solve this problem**.

Example:
Imagine you want to write a base class to describe **how the GROMACS software runs**, and then compose it with another set of classes that control **Spack software installation**.

**Without mixins:**
- You **cannot inherit from both** the Spack base class and the GROMACS base class due to multiple inheritance restrictions.

**With mixins:**
- You can **flexibly combine** different features (e.g., Spack, EasyBuild, Containers, Manual installations) without inheritance conflicts.

This enables **modular and scalable test design**, making it easy to support multiple configurations **without duplicating code**.

---

### **Avoiding Variable Name Clashes in Mixins**

While ReFrame’s variables are convenient (as they allow changes via command-line arguments), using **too many variables in mixins** introduces a risk:

**Problem:**
- If two mixins define a variable with the **same name**, they **cannot be composed together**.

**Solution:**
- This library minimizes the use of variables to ensure **mixins remain composable**.

---

### **Making Tests Ready to Use**

🔹 **All tests use ReFrame’s default built-in programming environment (`builtin`)**
🔹 **No additional command-line arguments** are needed to run them
🔹 **They are fully functional out-of-the-box**

This design ensures that users can **run tests immediately** without worrying about additional configurations.

---

### **Summary of Key Benefits**

✔ **Separation of test logic and system-specific details**
✔ **Composability through mixins** instead of rigid inheritance
✔ **Supports multiple software deployment methods (Spack, EasyBuild, Containers, etc.)**
✔ **Avoids variable conflicts to keep mixins compatible**
✔ **Tests are pre-configured and ready to run without extra setup**

Would you like to include an **example usage section** or a **quick start guide**?

## **Installation & Setup**

It is recommended to use this repository as a submodule inside your own, allowing for a better versioning control.

### **Prerequisites**
Ensure you have the following installed on your system:

- **Python 3.7+**
- **[ReFrame](https://github.com/reframe-hpc/reframe)** (the HPC testing framework)
- For most tests, a supported **batch scheduler** (e.g., SLURM, PBS, LSF) is required

### **Clone the Repository**
```bash
git clone https://github.com/victorusu/reframe-tests-library.git
cd reframe-test-library
```

### **Configuring ReFrame**

Make sure to have a properly configured ReFrame configuration file  to match your **HPC** or **testing environment**.
Ensure the **job scheduler**, **compute nodes**, and **partition features** settings are correctly defined.

## **Usage**

The library includes both **check mixins to develop your own tests** and **ready-to-run tests**.
The check mixins provide a a baseline that can be used to develop your own tests based on the supported cases from the library.
The ready-to-run tests leverage these baselines to implement a variety of tests for different environments with minimal modification.

You can decide to base your tests from the check mixins or inherit directly from the example tests.

### **Running Ready-to-Use Tests**
You can directly run the **predefined tests** included in the library using ReFrame:
```bash
reframe -c hpctestslib/checks -C <YOUR-SYSTEM-CONFIG> -R  -r
```

For more information on how to run ReFrame, please consult the [ReFrame documentation](https://reframe-hpc.readthedocs.io).

### **Writing Your Own Tests**

### **Starting from the Check Mixins**
To create a new test using the library, inherit from `RegressionMixin`.
Check the code and the documentation to find out about the specific details of
the mixin implementation.

An example for SPH-EXA is
```python
import reframe as rfm

import hpctestslib.util as hpcutil
import hpctestslib.mixin.sciapp.sphexa.mixin as sphexa


class sphexa_cpuonly_example_check(rfm.RunOnlyRegressionTest,
                                   sphexa.sphexa_mixin):

    num_nodes = parameter([1, 2])
    partition_cpus = parameter(hpcutil.get_max_cpus_per_part(),
                               fmt=lambda x: f'{util.toalphanum(x["name"]).lower()}_{x["num_cores"]}')
    valid_prog_environs = ['builtin']
    num_steps = 50 # mixin requires to define the num_steps of the simulation
    num_particles = 50 # mixin requires to define the num_particles in the simulation

    @run_after('init')
    def set_num_particles(self):
        # weak scaling example
        self.num_particles = self.num_particles * self.num_nodes

    @run_after('init')
    def setup_job_parameters(self):
        self.valid_systems = self.partition_cpus['fullname']
        self.num_cpus_per_task = self.partition_cpus['num_cores']
        self.num_tasks_per_node = self.partition_cpus['max_num_cores'] // self.num_cpus_per_task
        self.num_tasks = self.num_nodes * self.num_tasks_per_node
```

### **Starting from the Example Checks**

An example of strong-scaling SPH-EXA check that requires the `SPH-EXA`, `SPH-EXA-CUDA`, or `SPH-EXA-HIP` modules to be
loaded.
```python
import reframe as rfm

import hpctestslib.util as hpcutil
import hpctestslib.checks.sciapp.sphexa.benbenchmarks as sphexa


class sphexa_modules_strong_scaling_check(sphexa.sphexa_strong_scaling_check):
    # increasing the small num_particles defined in the library
    num_particles = 200

    @run_before('run')
    def set_modules(self):
        if self.accel == 'cuda':
            self.modules = ['SPH-EXA-CUDA']
        elif self.accel == 'hip':
            self.modules = ['SPH-EXA-HIP']
        else:
            self.modules = ['SPH-EXA']
```


An example of weak-scaling SPH-EXA check inheriting from the strong-scaling one
that also requires the same modules as above. The library already provides a weak
scaling test for convinience. But let's see how one can create a weak-scaling
test for SPH-EXA based on the strong-scaling one.
```python
import reframe as rfm

import hpctestslib.util as hpcutil
import hpctestslib.checks.sciapp.sphexa.benbenchmarks as sphexa


class sphexa_modules_weak_scaling_check(sphexa.sphexa_strong_scaling_check):
    # increasing the small num_particles defined in the library
    num_particles = 200

    @run_after('init')
    def set_modules(self):
        if self.accel == 'cuda':
            self.modules = ['SPH-EXA-CUDA']
        elif self.accel == 'hip':
            self.modules = ['SPH-EXA-HIP']
        else:
            self.modules = ['SPH-EXA']

    @run_after('init')
    def set_num_particles(self):
        self.num_particles = self.num_particles * self.num_nodes
```

Alternatively, if you define both checks in the same file it is convenient to
just write one and make the other inherit from the first.
```python
import reframe as rfm

import hpctestslib.util as hpcutil
import hpctestslib.checks.sciapp.sphexa.benbenchmarks as sphexa


class sphexa_modules_strong_scaling_check(sphexa.sphexa_strong_scaling_check):
    # increasing the small num_particles defined in the library
    num_particles = 200

    @run_before('run')
    def set_modules(self):
        if self.accel == 'cuda':
            self.modules = ['SPH-EXA-CUDA']
        elif self.accel == 'hip':
            self.modules = ['SPH-EXA-HIP']
        else:
            self.modules = ['SPH-EXA']


class sphexa_modules_weak_scaling_check(sphexa_modules_strong_scaling_check):
    @run_after('init')
    def set_num_particles(self):
        self.num_particles = self.num_particles * self.num_nodes
```

## **Example Output**

When running a test, you should see an output similar to:

```bash
[==========] Running 2 check(s)
[ RUN      ] my_test@rocky:login+builtin
[       OK ] ( 1/2) my_test@rocky:login+builtin /89a8dad0 @rocky:login+builtin
[ RUN      ] another_test@rocky:login+builtin
[       OK ] ( 2/2) another_test@rocky:login+builtin /9a0f69be @rocky:login+builtin
[==========] Ran 2 test(s) in 6.0s
[  PASSED  ] Ran 2/2 test case(s) from 1 check(s) (0 failure(s), 0 skipped, 0 aborted)
```

## **Contributing**
We welcome contributions! To add new tests or improve the library:

1. **Fork** the repository
2. **Create** a new feature branch
3. **Submit** a pull request with your changes

## **License**
This project is licensed under the **BSD-3-Clause License**. See the [LICENSE](LICENSE) file for details.
