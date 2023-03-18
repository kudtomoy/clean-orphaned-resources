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

## Installation
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
By default, only the default region will be listed. To list all regions, use the `--all-regions (-a)` option.

See the `--help (-h)` command for all options.

```bash
$ clean-orphaned-resources list -a > orphaned_resources.txt
```

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

## Advanced Topics
If you have named resources that you do not want to delete, you can exclude them from the list as follows:
```bash
$ clean-orphaned-resources list | grep -v do-not-delete > orphaned_resources.txt
```

When destroying, the `#` after each line is ignored and can be used as your comment space.
```txt
ap-northeast-1,AWS::Logs::LogGroup,/test-log-group,#<YourComment>
```

## Running pytest
**Note**: These tests create and remove resources in a real AWS environment. Be sure to use your test AWS account and read the code beforehand.

1. Install requirements for tests.
```bash
$ pip3 install -r dev-requirements.txt
```

2. If necessary, add the current directory to `PYTHONPATH`.
```bash
$ export PYTHONPATH=$PYTHONPATH:`pwd`
```

3. Run tests.
```bash
$ pytest tests
```
