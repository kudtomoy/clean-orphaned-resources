# clean-orphaned-resources

A CLI tool to clean up orphaned AWS resources that remain after AWS CDK destroys stacks.

## Supported orphaned resources
- `AWS::Logs::LogGroup`
- `AWS::DynamoDB::Table`
- `AWS::ECR::Repository`
- `AWS::EFS::FileSystem`
- `AWS::KMS::Key`
- `AWS::S3::Bucket`

## Requirements
- Python 3.7 or later

## Install
```bash
$ pip3 install git+https://github.com/kudtomoy/clean-orphaned-resources.git
```

If you want to uninstall:
```bash
$ pip3 uninstall clean-orphaned-resources
```

The `clean-orphaned-resources` is installed as an executable file.  
If needed, add its location to your system's PATH. Here's an example on my Mac:
```bash
$ export PATH=$PATH:$HOME/Library/Python/3.9/bin
```

## Usage
1. List and save orphaned resources:
```bash
$ clean-orphaned-resources list > orphaned_resources.txt
```
This command lists all orphaned resources that are not associated with any CloudFormation stacks.


2. Review the list and manually remove any resources you do NOT want to delete.  
The standard output file is formatted as follows.
```txt
<Region>,<ResourceType>,<ReouceName or ID>,<Tags>
```

3. Delete the orphaned resources listed in the file:
```bash
$ clean-orphaned-resources destroy < orphaned_resources.txt
```
This command deletes all resources listed in the `orphaned_resources.txt` file.

**Note**: Be cautious when using the `destroy` command, as it will permanently delete the specified resources. Always review the list of resources to be deleted and make sure you have backups if necessary.
