import boto3
from botocore.exceptions import ClientError
import time

# --- Configuration ---
AWS_REGION = "eu-north-1"

# Replace with your actual VPC ID, Subnet IDs, and EC2 Instance ID
VPC_ID = "vpc-04d79fb7a347a0060" 
SUBNET_IDS = ["subnet-04905f299f1aef81d", "subnet-03507a7af79c9360a", "subnet-060cc81012213f684"]
EC2_INSTANCE_ID = "i-0f22544baa8b50f6f"

# --- AWS Clients ---
elb_client = boto3.client("elbv2", region_name=AWS_REGION)
ec2_client = boto3.client("ec2", region_name=AWS_REGION)

def create_security_group(vpc_id):
    """Creates a security group for the ELB and EC2 instance, allowing necessary traffic."""
    sg_name = "java-app-elb-sg"
    description = "Security group for Java application ELB and EC2"

    try:
        response = ec2_client.describe_security_groups(Filters=[
            {'Name': 'group-name', 'Values': [sg_name]},
            {'Name': 'vpc-id', 'Values': [vpc_id]}
        ])
        if response['SecurityGroups']:
            print(f"Security group {sg_name} already exists. Using existing one.")
            return response['SecurityGroups'][0]['GroupId']
    except ClientError as e:
        if "DoesNotExist" not in str(e):
            print(f"Error describing security groups: {e}")
            exit(1)

    print(f"Creating security group {sg_name}...")
    try:
        response = ec2_client.create_security_group(
            GroupName=sg_name,
            Description=description,
            VpcId=vpc_id
        )
        sg_id = response['GroupId']
        print(f"Security Group created: {sg_id}")

        # Allow HTTP (port 80) for ALB inbound
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
        # Allow custom port (8080) for EC2 inbound from ALB
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8080,
                    'ToPort': 8080,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}] # This should ideally be restricted to ALB SG
                }
            ]
        )
        print(f"Ingress rules added to {sg_id}")
        return sg_id
    except ClientError as e:
        print(f"Error creating security group: {e}")
        exit(1)

def create_elastic_load_balancer(
    vpc_id, subnet_ids, ec2_instance_id, security_group_id
):
    """Creates an AWS Application Load Balancer, Target Group, and Listener."""
    elb_name = "java-app-elb"
    tg_name = "java-app-tg"

    # --- Comprehensive Deletion Logic (delete in reverse order of creation) ---
    # 1. Attempt to delete existing Listeners
    print(f"Attempting to delete existing Listeners for {elb_name}...")
    try:
        elb_response = elb_client.describe_load_balancers(Names=[elb_name])
        existing_elb_arn = elb_response['LoadBalancers'][0]['LoadBalancerArn']
        listeners_response = elb_client.describe_listeners(LoadBalancerArn=existing_elb_arn)
        for listener in listeners_response.get('Listeners', []):
            print(f"Deleting listener: {listener['ListenerArn']}...")
            elb_client.delete_listener(ListenerArn=listener['ListenerArn'])
            print("Listener deleted.")
        print("Finished attempting to delete listeners.")
    except ClientError as e:
        if "LoadBalancerNotFound" not in str(e) and "ListenerNotFound" not in str(e):
            print(f"Error during listener deletion: {e}")
        print("No existing listeners or load balancer found to delete, or encountered non-critical error.")

    # 2. Attempt to delete existing Target Groups
    print(f"Attempting to delete existing Target Group {tg_name}...")
    try:
        tg_response = elb_client.describe_target_groups(Names=[tg_name])
        if tg_response['TargetGroups']:
            existing_tg_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
            print(f"Deleting Target Group: {existing_tg_arn}...")
            elb_client.delete_target_group(TargetGroupArn=existing_tg_arn)
            print("Target Group deleted.")
        print("Finished attempting to delete target groups.")
    except ClientError as e:
        if "TargetGroupNotFound" not in str(e):
            print(f"Error during target group deletion: {e}")
        print("No existing target group found to delete, or encountered non-critical error.")

    # 3. Attempt to delete existing Load Balancer
    print(f"Attempting to delete existing Load Balancer {elb_name}...")
    try:
        elb_response = elb_client.describe_load_balancers(Names=[elb_name])
        if elb_response['LoadBalancers']:
            existing_elb_arn = elb_response['LoadBalancers'][0]['LoadBalancerArn']
            print(f"Deleting Load Balancer: {existing_elb_arn}...")
            elb_client.delete_load_balancer(LoadBalancerArn=existing_elb_arn)
            print("Load Balancer deleted.")
        print("Finished attempting to delete load balancer.")
    except ClientError as e:
        if "LoadBalancerNotFound" not in str(e):
            print(f"Error during load balancer deletion: {e}")
        print("No existing load balancer found to delete, or encountered non-critical error.")

    # Give AWS a moment to fully de-provision resources (important for clean recreation)
    print("Waiting for resources to fully de-provision (10 seconds)...")
    time.sleep(10)
    # --- End Comprehensive Deletion Logic ---

    # 1. Create Application Load Balancer
    print(f"Creating Application Load Balancer {elb_name}...")
    try:
        response = elb_client.create_load_balancer(
            Name=elb_name,
            Subnets=subnet_ids,
            SecurityGroups=[security_group_id],
            Scheme="internet-facing",
            Type="application",
            IpAddressType="ipv4"
        )
        load_balancer_arn = response['LoadBalancers'][0]['LoadBalancerArn']
        print(f"Load Balancer created: {load_balancer_arn}")
    except ClientError as e:
        print(f"Error creating Load Balancer: {e}")
        exit(1)

    # 2. Create Target Group
    print(f"Creating Target Group {tg_name} with port 8080...")
    try:
        response = elb_client.create_target_group(
            Name=tg_name,
            Protocol="HTTP",
            Port=8080,
            VpcId=vpc_id,
            HealthCheckProtocol="HTTP",
            HealthCheckPort="8080",
            HealthCheckPath="/",  # Assuming root path for health check
            HealthCheckIntervalSeconds=30,
            HealthCheckTimeoutSeconds=5,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=2
        )
        target_group_arn = response['TargetGroups'][0]['TargetGroupArn']
        print(f"Target Group created: {target_group_arn}")
    except ClientError as e:
        print(f"Error creating Target Group: {e}")
        exit(1)

    # 3. Register EC2 instance with Target Group
    print(f"Registering instance {ec2_instance_id} with Target Group...")
    try:
        elb_client.register_targets(
            TargetGroupArn=target_group_arn,
            Targets=[{"Id": ec2_instance_id}]
        )
        print(f"Instance {ec2_instance_id} registered with {target_group_arn}")
    except ClientError as e:
        print(f"Error registering target: {e}")
        exit(1)

    # 4. Create Listener
    print(f"Creating Listener for {elb_name} on port 80...")
    try:
        elb_client.create_listener(
            LoadBalancerArn=load_balancer_arn,
            Protocol="HTTP",
            Port=80,
            DefaultActions=[
                {
                    "Type": "forward",
                    "TargetGroupArn": target_group_arn,
                }
            ],
        )
        print("Listener created successfully on port 80.")
    except ClientError as e:
        print(f"Error creating Listener: {e}")
        exit(1)

    print(f"ELB setup complete. Access your application via the ELB DNS name.")

if __name__ == "__main__":
    # Ensure boto3 is installed: pip install boto3
    # Ensure your AWS credentials are configured (e.g., via AWS CLI or environment variables)
    
    if VPC_ID == "vpc-xxxxxxxxxxxxxxxxx" or not SUBNET_IDS or EC2_INSTANCE_ID == "i-xxxxxxxxxxxxxxxxx":
        print("Please update VPC_ID, SUBNET_IDS, and EC2_INSTANCE_ID in the script before running.")
        exit(1)

    # Create or get security group
    sg_id = create_security_group(VPC_ID)

    # Create ELB components
    create_elastic_load_balancer(VPC_ID, SUBNET_IDS, EC2_INSTANCE_ID, sg_id) 