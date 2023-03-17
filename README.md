# clean-orphaned-resources

A CLI tool to clean up orphaned AWS resources that remain after AWS CDK destroys stacks.

## Requirements
- Python 3.7 or later

## Installing
```bash
$ pip3 install git+git://github.com/kudtomoy/clean-orphaned-resources.git
```

## Usage
1. List and save orphaned resources:
```bash
$ clean-orphaned-resources list > orphaned_resources.txt
```
This command lists all orphaned resources that are not associated with any CloudFormation stacks.


2. Review the list and manually remove any resources you do not want to delete.

3. Delete the orphaned resources listed in the file:
```bash
$ clean-orphaned-resources destroy < orphaned_resources.txt
```
This command deletes all resources listed in the `orphaned_resources.txt` file.

**Note**: Be cautious when using the `destroy` command, as it will permanently delete the specified resources. Always review the list of resources to be deleted and make sure you have backups if necessary.
