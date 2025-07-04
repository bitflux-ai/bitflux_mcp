import sys
import server
import server.downloadstats
import server.ec2_tools
import server.machine_lookup

if len(sys.argv) > 1:
    match sys.argv[1]:
        case "downloadstats":
            sys.argv.pop(1)
            server.downloadstats.manual()
        case "ec2_instances":
            sys.argv.pop(1)
            server.ec2_tools.ec2_instances.manual()
        case "ec2_pricing":
            sys.argv.pop(1)
            server.ec2_tools.ec2_pricing.manual()
        case "ec2_account":
            sys.argv.pop(1)
            print(server.ec2_tools.ec2_account.get_aws_account_id())
        case "ec2_ami":
            sys.argv.pop(1)
            server.ec2_tools.ec2_ami.manual()
        case "machine_lookup":
            sys.argv.pop(1)
            server.machine_lookup.tool.manual()
        case _:
            server.main()
else:
    server.main()
