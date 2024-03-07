# ApplicationManager---Change-Job-Status

py. Application MUST BE converted into .exe with PYInstaller

# Short Introduction

**Original Use Case:** Customer wants to have an automatic job that checks all jobs in the item where the job is run and wants to change their status to "Without Invoice" if the job follows certain criteria.

**Definition:** Application that receives information via ApplicationManager, finds respective jobs and changes their status accordingly.

## Application Requirements

### General Requirements

- It shall be possible to configure the specific parameters for the script:
  - Definition of a Plunet property and its allowed values.
  - Definition of allowed status.
  - Definition of target status.
  - User name and password and URL for the Plunet API.

### Workflow

#### Starting the Application

- The application shall be able to receive order number and language combination (to identify the corresponding item of a job).
- The application shall be able to receive storing location of configuration file with ApplicationManager call.

#### Preparation

- Create a log file in Job _IN Folder.
- Retrieve configuration.
- Retrieve parameters passed along by ApplicationManager.

#### Finding the Jobs of the Corresponding Item Where the Application Manager Job Is

- Login into Plunet API.
- Find Order (API Call).
- Find respective item by Source and target language (API Call).
- Retrieve all jobs in item (API Call).

#### Analyse all Jobs in Item

- Check if jobs are in the allowed status defined in the configuration file (API Call).
- Check if jobs have a resource applied to them (API Call).
  - No Resource: set status to defined target status from config file.
  - Resource set: Check if resource property from config file has an allowed value:
    - YES - allowed value set: set status to defined target status from config file.
    - IGNORE IF DATA LOCKED.

# Configuration

## File Location

- Executable and configuration file shall be stored on the server where Plunet runs.

## Plunet Job Configuration
[config](https://github.com/PlunetBusinessManager/ApplicationManager---Change-Job-Status/blob/main/config_pic.png)

### Parameters

- Example: `C:\Plunet\App\job_change_script.exe [OrderNo] [Languages] "C:\Plunet\App"`
- Explanation:
  - `EXECUTABLE FILE LOCATION` || Plunet Flag for Order Number || Plunet Flag for Language Combination || Location of the configuration File

