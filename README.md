# GDrive2Insta
# Automated Instagram Uploader with Oracle Cloud VM

This guide will walk you through setting up a Python script on a free Oracle Cloud Virtual Machine (VM) to automatically upload images from a Google Drive folder to Instagram. This setup allows for continuous operation, 24/7, without requiring your local machine to be constantly running.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setting up an Oracle Cloud VM](#setting-up-an-oracle-cloud-vm)
   - [Creating an Oracle Cloud Account](#creating-an-oracle-cloud-account)
   - [Launching a VM Instance](#launching-a-vm-instance)
   - [Connecting to Your VM](#connecting-to-your-vm)
   - [Configuring the VM](#configuring-the-vm)
3. [Installing Dependencies](#installing-dependencies)
4. [Setting up Google Drive Access](#setting-up-google-drive-access)
5. [Configuring Instagram Access](#configuring-instagram-access)
6. [Uploading and running the Script](#uploading-the-script)
7. [Testing the Script](#testing-the-script)


## Prerequisites

- **Oracle Cloud Account**: You'll need a free Oracle Cloud account.
- **Google Account**: A Google account with Google Drive access.
- **Instagram Account**: An Instagram account.
- **Basic Linux Knowledge**: Familiarity with basic Linux commands is helpful.

## Setting up an Oracle Cloud VM

### Creating an Oracle Cloud Account

1. Go to the [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) page.
2. Click **"Start for free"** and follow the instructions to create your account. You will need to provide a credit card, but you won’t be charged for the free tier resources unless you upgrade.
3. Once your account is set up, sign in to the Oracle Cloud Infrastructure (OCI) console.

### Launching a VM Instance

1. In the OCI console, navigate to **Compute > Instances**.
2. Click **"Create Instance"**.
3. Provide a name for your instance (e.g., `InstagramUploaderVM`).
4. **Image and shape**:
   - Select **Ubuntu** as the operating system (Tested with Ubuntu 20.04 and 22.04).
   - Choose one of the **"Always Free Eligible"** shapes (e.g., `VM.Standard.A1.Flex`) with 1 OCPU and 1 GB of memory.
5. **Add SSH Keys**:
   - Choose **"Generate SSH Key Pair"**.
   - Download the private key file (e.g., `id_rsa`). **Keep it safe**.
6. Click **Create**. Your instance will launch, and its status will change to **"Running"**.
### Enabling Internet Access on Oracle Cloud VM
#### Step 1: Create/Check VCN and Subnet
1. Go to the Oracle Cloud Console.
2. Navigate to:
```bash
Networking > Virtual Cloud Networks
```
3. Check your VM’s VCN:
- When you created your instance, a VCN (Virtual Cloud Network) and subnet were automatically created unless you chose an existing one.
4. Click on your VCN, and verify it includes:
- Subnet
- Internet Gateway
- Route Table
#### Step 2: Add an Internet Gateway (if missing)
1. In your VCN, click "Internet Gateways" (left panel).
2. Click Create Internet Gateway, name it (e.g., IGW-For-VM), and create.
3. Go to Route Tables in the same VCN.
4. Click on the route table used by your subnet (e.g., Default Route Table for VCN).
5. Click Add Route Rule:
- Target Type: Internet Gateway
- Destination CIDR Block: 0.0.0.0/0
- Target: Select the internet gateway you just created
#### Step 3: Set the Subnet to Public
If you want the VM to be accessible from the internet:
1. In your subnet configuration, check Public Subnet is enabled.
2. Ensure Auto-assign public IP address is enabled when launching the VM (or manually assign a public IP if not).
#### Step 4: Configure Security List (Firewall)
1. Go to Networking > Virtual Cloud Networks > Your VCN > Security Lists.
2. Click the security list associated with your subnet (e.g., Default Security List for VCN).
3. Add the following Ingress Rules to allow SSH, HTTP, and VNC:
| Protocol | Port Range | Source CIDR | Purpose    |
| -------- | ---------- | ----------- | ---------- |
| TCP      | 22         | 0.0.0.0/0   | SSH        |
| TCP      | 5901-5910  | 0.0.0.0/0   | VNC access |
| TCP      | 80, 443    | 0.0.0.0/0   | Web access |
4. Add an Egress Rule:
- Destination CIDR: 0.0.0.0/0
- All Protocols: Allow all outbound traffic

### Connecting to Your VM

1. Open a terminal on your local machine.
2. Change the permissions of your private key file:
   ```bash
   chmod 400 /path/to/your/id_rsa  # Replace with actual path to your private key
  
   ssh -i /path/to/your/id_rsa ubuntu@<your_public_ip> # Have a look at your VM Networking infos. You will find it.


## Configuring the VM
### 📦 Installing Dependencies

Update and install required packages:
 ```bash
 sudo apt update && sudo apt upgrade -y
 sudo apt install python3 python3-pip git unzip -y 
 pip3 install instagrapi google-auth google-auth-oauthlib google-api-python-client 
 ```
## Setting up Google Drive Access
1. Go to the Google Cloud Console.

2. Create a new project or use an existing one.

3. Enable the Google Drive API:

- In the navigation menu, go to APIs & Services > Library.

- Search for Google Drive API and click Enable.

4. Create credentials:
- Navigate to APIs & Services > Credentials.

- Click Create Credentials > OAuth client ID.

- Choose Desktop App and download the **credentials.json** file.

5. Upload this file to your VM:
```bash
scp -i /path/to/your/id_rsa credentials.json ubuntu@<your_public_ip>:~
```
6. When running your script for the first time, it will open a browser link. Open it on your local machine, authorize, and paste the token if required. This will create a token.json for future authentication.

## Configuring Instagram Access
### The script uses instagrapi to log in and upload posts.
### 🔐 Instagram Login
You can store your credentials securely in a .env file or hardcode them (not recommended for production).

Example:
```bash
from instagrapi import Client

cl = Client()
cl.login("your_username", "your_password")
```
- 🛑 Instagram may temporarily block cloud logins or require challenge verification. Use a real device first to build trust.

## Uploading the Script
1. Save your Python script as insta.py
2. Use scp to upload:
```bash
scp -i /path/to/your/id_rsa insta.py ubuntu@<your_public_ip>:~
```
3. Ensure it's executable:
```bash
chmod +x insta.py
```
### Running the Script
```bash
python3 insta.py
```


## Testing the Script
1. Place an image in your Google Drive folder.

2. Wait for the script to detect and upload it.

3. Check Instagram for the new post and output.log for logs
