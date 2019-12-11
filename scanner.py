#!/usr/bin/python
# -*- coding: utf-8 -*-
#                               __
#                              (   _  _
#                             __) (_ (/ /)
#
#
# Author	 : Halashankara
# Tool 		 : Scanner
# Usage		 : ./scanner.py example.com (or) python scanner.py example.com
# Description: This scanner automates the process of security scanning by using a
#              multitude of available linux security tools and some custom scripts.
#

# Importing the libraries
import sys
import socket
import subprocess
import os
import time
import signal
import random
import string
import threading
import re
from urlparse import urlsplit


# Scan Time Elapser
intervals = (
    ('h', 3600),
    ('m', 60),
    ('s', 1),
)


def display_time(seconds, granularity=3):
    result = []
    seconds = seconds + 1
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            result.append("{}{}".format(value, name))
    return ' '.join(result[:granularity])


def url_maker(url):
    if not re.match(r'http(s?)\:', url):
        url = 'http://' + url
    parsed = urlsplit(url)
    host = parsed.netloc
    if host.startswith('www.'):
        host = host[4:]
    return host


def check_internet():
    os.system('ping -c1 github.com > rs_net 2>&1')
    if "0% packet loss" in open('rs_net').read():
        val = 1
    else:
        val = 0
    os.system('rm rs_net > /dev/null 2>&1')
    return val


# Initializing the color module class
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    BADFAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    BG_ERR_TXT = '\033[41m'  # For critical errors and crashes
    BG_HEAD_TXT = '\033[100m'
    BG_ENDL_TXT = '\033[46m'
    BG_CRIT_TXT = '\033[45m'
    BG_HIGH_TXT = '\033[41m'
    BG_MED_TXT = '\033[43m'
    BG_LOW_TXT = '\033[44m'
    BG_INFO_TXT = '\033[42m'


# Classifies the Vulnerability's Severity
def vul_info(val):
    result = ''
    if val == 'c':
        result = bcolors.BG_CRIT_TXT+" critical "+bcolors.ENDC
    elif val == 'h':
        result = bcolors.BG_HIGH_TXT+" high "+bcolors.ENDC
    elif val == 'm':
        result = bcolors.BG_MED_TXT+" medium "+bcolors.ENDC
    elif val == 'l':
        result = bcolors.BG_LOW_TXT+" low "+bcolors.ENDC
    else:
        result = bcolors.BG_INFO_TXT+" info "+bcolors.ENDC
    return result


# Legends
proc_high = bcolors.BADFAIL + "●" + bcolors.ENDC
proc_med = bcolors.WARNING + "●" + bcolors.ENDC
proc_low = bcolors.OKGREEN + "●" + bcolors.ENDC

# Links the vulnerability with threat level and remediation database


def vul_remed_info(v1, v2, v3):
    print bcolors.BOLD+"Vulnerability Threat Level"+bcolors.ENDC
    print "\t"+vul_info(v2)+" "+bcolors.WARNING + \
        str(tool_resp[v1][0])+bcolors.ENDC
    print bcolors.BOLD+"Vulnerability Definition"+bcolors.ENDC
    print "\t"+bcolors.BADFAIL+str(tools_fix[v3-1][1])+bcolors.ENDC
    print bcolors.BOLD+"Vulnerability Remediation"+bcolors.ENDC
    print "\t"+bcolors.OKGREEN+str(tools_fix[v3-1][2])+bcolors.ENDC


# RapidScan Help Context
def helper():
    print bcolors.OKBLUE+"Information:"+bcolors.ENDC
    print "------------"
    print "\t./scanner.py example.com: Scans the domain example.com"
    print "\t./scanner.py --update   : Updates the scanner to the latest version."
    print "\t./scanner.py --help     : Displays this help context."
    print bcolors.OKBLUE+"Interactive:"+bcolors.ENDC
    print "------------"
    print "\tCtrl+C: Skips current test."
    print "\tCtrl+Z: Quits RapidScan."
    print bcolors.OKBLUE+"Legends:"+bcolors.ENDC
    print "--------"
    print "\t["+proc_high + \
        "]: Scan process may take longer times (not predictable)."
    print "\t["+proc_med+"]: Scan process may take less than 10 minutes."
    print "\t["+proc_low+"]: Scan process may take less than a minute or two."
    print bcolors.OKBLUE+"Vulnerability Information:"+bcolors.ENDC
    print "--------------------------"
    print "\t" + \
        vul_info(
            'c')+": Requires immediate attention as it may lead to compromise or service unavailability."
    print "\t" + \
        vul_info(
            'h')+"    : May not lead to an immediate compromise, but there are high chances of probability."
    print "\t" + \
        vul_info(
            'm')+"  : Attacker may correlate multiple vulnerabilities of this type to launch a sophisticated attack."
    print "\t" + \
        vul_info(
            'l')+"     : Not a serious issue, but it is recommended to attend the finding."
    print "\t" + \
        vul_info(
            'i')+"    : Not classified as a vulnerability, simply an useful informational alert to be considered.\n"


# Clears Line
def clear():
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")

# RapidScan Logo


def logo():
    print bcolors.WARNING
    print("""
                            """)
    print bcolors.ENDC

# Initiliazing the idle loader/spinner class


class Spinner:
    busy = False
    delay = 0.05

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in '( )( )':
                yield cursor  # ←↑↓→
            # for cursor in '←↑↓→': yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay):
            self.delay = delay

    def spinner_task(self):
        try:
            while self.busy:
                # sys.stdout.write(next(self.spinner_generator))
                print bcolors.BG_ERR_TXT + \
                    next(self.spinner_generator)+bcolors.ENDC,
                sys.stdout.flush()
                time.sleep(self.delay)
                sys.stdout.write('\b')
                sys.stdout.flush()
        except (KeyboardInterrupt, SystemExit):
            # clear()
            print "\n\t" + bcolors.BG_ERR_TXT + \
                "Scanner received a series of Ctrl+C hits. Quitting..." + bcolors.ENDC
            sys.exit(1)

    def start(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def stop(self):
        try:
            self.busy = False
            time.sleep(self.delay)
        except (KeyboardInterrupt, SystemExit):
            # clear()
            print "\n\t" + bcolors.BG_ERR_TXT + \
                "Scanner received a series of Ctrl+C hits. Quitting..." + bcolors.ENDC
            sys.exit(1)
# End ofloader/spinner class


# Instantiating the spinner/loader class
spinner = Spinner()

# Scanners that will be used and filename rotation (default: enabled (1))
tool_names = [
    ["host", "Host - Checks for existence of IPV6 address.", "host", 1],
    ["wp_check","WordPress Checker - Checks for WordPress Installation.","wget",1],
    ["uniscan","Uniscan - Checks for robots.txt & sitemap.xml","uniscan",1],
    ["wafw00f","Wafw00f - Checks for Application Firewalls.","wafw00f",1],
    ["nmap","Nmap - Fast Scan [Only Few Port Checks]","nmap",1],
]

# Command that is used to initiate the tool (with parameters and extra params)
tool_cmd = [
    ["host ", ""],
    ["wget -O temp_wp_check --tries=1 ","/wp-admin"],
    ["uniscan -e -u ",""],
    ["wafw00f ",""],
    ["nmap -F --open -Pn ",""],
]

# Tool Responses (Begins) [Responses + Severity (c - critical | h - high | m - medium | l - low | i - informational) + Reference for Vuln Definition and Remediation]
tool_resp = [
    ["Does not have an IPv6 Address. It is good to have one.", "i", 1],
    ["WordPress Installation Found. Check for vulnerabilities corresponds to that version.","i",2],
    ["robots.txt/sitemap.xml found. Check those files for any information.","i",3],
    ["No Web Application Firewall Detected","m",4],
    ["Some ports are open. Perform a full-scan manually.","l",5],
]
# Tool Responses (Ends)

# Tool Status (Response Data + Response Code (if status check fails and you still got to push it + Legends + Approx Time + Tool Identification + Bad Responses)
tool_status = [
    ["has IPv6", 1, proc_low, " < 15s", "ipv6", ["not found", "has IPv6"]],
    ["wp-login",0,proc_low," < 30s","wpcheck",["unable to resolve host address","Connection timed out"]],
    ["[+]",0,proc_low," < 40s","robotscheck",["Use of uninitialized value in unpack at"]],
    ["No WAF",0,proc_low," < 45s","wafcheck",["appears to be down"]],
    ["tcp open",0,proc_med," <  2m","nmapopen",["Failed to resolve"]],
]

# Vulnerabilities and Remediation
tools_fix = [
    [1, "Not a vulnerability, just an informational alert. The host does not have IPv6 support. IPv6 provides more security as IPSec (responsible for CIA - Confidentiality, Integrity and Availablity) is incorporated into this model. So it is good to have IPv6 Support.",
     "It is recommended to implement IPv6. More information on how to implement IPv6 can be found from this resource. https://www.cisco.com/c/en/us/solutions/collateral/enterprise/cisco-on-cisco/IPv6-Implementation_CS.html"],
    [2, "It is not bad to have a CMS in WordPress. There are chances that the version may contain vulnerabilities or any third party scripts associated with it may possess vulnerabilities",
							"It is recommended to conceal the version of WordPress. This resource contains more information on how to secure your WordPress Blog. https://codex.wordpress.org/Hardening_WordPress"],
    [3, "Sometimes robots.txt or sitemap.xml may contain rules such that certain links that are not supposed to be accessed/indexed by crawlers and search engines. Search engines may skip those links but attackers will be able to access it directly.",
							"It is a good practice not to include sensitive links in the robots or sitemap files."],
	[4, "Without a Web Application Firewall, An attacker may try to inject various attack patterns either manually or using automated scanners. An automated scanner may send hordes of attack vectors and patterns to validate an attack, there are also chances for the application to get DoS`ed (Denial of Service)",
							"Web Application Firewalls offer great protection against common web attacks like XSS, SQLi, etc. They also provide an additional line of defense to your security infrastructure. This resource contains information on web application firewalls that could suit your application. https://www.gartner.com/reviews/market/web-application-firewall"],
	[5, "Open Ports give attackers a hint to exploit the services. Attackers try to retrieve banner information through the ports and understand what type of service the host is running",
							"It is recommended to close the ports of unused services and use a firewall to filter the ports wherever necessary. This resource may give more insights. https://security.stackexchange.com/a/145781/6137"],
]


# Tool Set
tools_precheck = [
    ["wapiti"], ["whatweb"], ["nmap"], ["golismero"], ["host"], ["wget"], ["uniscan"], ["wafw00f"], ["dirb"], ["davtest"], ["theharvester"], ["xsser"], [
        "dnsrecon"], ["fierce"], ["dnswalk"], ["whois"], ["sslyze"], ["lbd"], ["golismero"], ["dnsenum"], ["dmitry"], ["davtest"], ["nikto"], ["dnsmap"]
]

# Shuffling Scan Order (starts)
scan_shuffle = list(zip(tool_names, tool_cmd, tool_resp, tool_status))
random.shuffle(scan_shuffle)
tool_names, tool_cmd, tool_resp, tool_status = zip(*scan_shuffle)
# Cross verification incase, breaks.
tool_checks = (len(tool_names) + len(tool_resp) + len(tool_status)) / 3
# Shuffling Scan Order (ends)

# Tool Head Pointer: (can be increased but certain tools will be skipped)
tool = 0

# Run Test
runTest = 1

# For accessing list/dictionary elements
arg1 = 0
arg2 = 1
arg3 = 2
arg4 = 3
arg5 = 4
arg6 = 5

# Detected Vulnerabilities [will be dynamically populated]
rs_vul_list = list()
rs_vul_num = 0
rs_vul = 0

# Total Time Elapsed
rs_total_elapsed = 0

# Tool Pre Checker
rs_avail_tools = 0

# Checks Skipped
rs_skipped_checks = 0

if len(sys.argv) == 1:
    logo()
    helper()
else:
    target = sys.argv[1].lower()

    if target == '--update' or target == '-u' or target == '--u':
        logo()
        print "Scanner is updating....Please wait.\n"
        spinner.start()
        # Checking internet connectivity first...
        rs_internet_availability = check_internet()
        if rs_internet_availability == 0:
            print "\t" + bcolors.BG_ERR_TXT + \
                "There seems to be some problem connecting to the internet. Please try again or later." + bcolors.ENDC
            spinner.stop()
            sys.exit(1)
        cmd = 'sha1sum scanner.py | grep .... | cut -c 1-40'
        oldversion_hash = subprocess.check_output(cmd, shell=True)
        oldversion_hash = oldversion_hash.strip()
        os.system(
            'wget -N https://github.com/halashankar/Scanner/master/scanner.py -O scanner.py > /dev/null 2>&1')
        newversion_hash = subprocess.check_output(cmd, shell=True)
        newversion_hash = newversion_hash.strip()
        if oldversion_hash == newversion_hash:
            clear()
            print "\t" + bcolors.OKBLUE + \
                "You already have the latest version of Scanner." + bcolors.ENDC
        else:
            clear()
            print "\t" + bcolors.OKGREEN + \
                "Scanner successfully updated to the latest version." + bcolors.ENDC
        spinner.stop()
        sys.exit(1)

    elif target == '--help' or target == '-h' or target == '--h':
        logo()
        helper()
        sys.exit(1)
    else:

        target = url_maker(target)
        os.system('rm te* > /dev/null 2>&1')  # Clearing previous scan files
        os.system('clear')
        os.system('setterm -cursor off')
        logo()
        print bcolors.BG_HEAD_TXT + \
            "[ Checking Available Security Scanning Tools Phase... Initiated. ]"+bcolors.ENDC
        unavail_tools = 0
        unavail_tools_names = list()
        while (rs_avail_tools < len(tools_precheck)):
            precmd = str(tools_precheck[rs_avail_tools][arg1])
            try:
                p = subprocess.Popen([precmd], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                output, err = p.communicate()
                val = output + err
            except:
                print "\t"+bcolors.BG_ERR_TXT+"RapidScan was terminated abruptly..."+bcolors.ENDC
                sys.exit(1)
            if "not found" in val:
                print "\t"+bcolors.OKBLUE + \
                    tools_precheck[rs_avail_tools][arg1]+bcolors.ENDC + \
                    bcolors.BADFAIL+"...unavailable."+bcolors.ENDC
                for scanner_index, scanner_val in enumerate(tool_names):
                    if scanner_val[2] == tools_precheck[rs_avail_tools][arg1]:
                        # disabling scanner as it's not available.
                        scanner_val[3] = 0
                        unavail_tools_names.append(
                            tools_precheck[rs_avail_tools][arg1])
                        unavail_tools = unavail_tools + 1
            else:
                print "\t"+bcolors.OKBLUE + \
                    tools_precheck[rs_avail_tools][arg1]+bcolors.ENDC + \
                    bcolors.OKGREEN+"...available."+bcolors.ENDC
            rs_avail_tools = rs_avail_tools + 1
            clear()
        unavail_tools_names = list(set(unavail_tools_names))
        if unavail_tools == 0:
            print "\t"+bcolors.OKGREEN + \
                "All Scanning Tools are available. All vulnerability checks will be performed by RapidScan."+bcolors.ENDC
        else:
            print "\t"+bcolors.WARNING+"Some of these tools "+bcolors.BADFAIL + \
                str(unavail_tools_names)+bcolors.ENDC+bcolors.WARNING + \
                " are unavailable. RapidScan can still perform tests by excluding these tools from the tests. Please install these tools to fully utilize the functionality of RapidScan."+bcolors.ENDC
        print bcolors.BG_ENDL_TXT + \
            "[ Checking Available Security Scanning Tools Phase... Completed. ]"+bcolors.ENDC
        print "\n"
        print bcolors.BG_HEAD_TXT+"[ Preliminary Scan Phase Initiated... Loaded "+str(
            tool_checks)+" vulnerability checks.  ]"+bcolors.ENDC
        # while (tool < 1):
        while(tool < len(tool_names)):
            print "["+tool_status[tool][arg3]+tool_status[tool][arg4]+"] Deploying "+str(
                tool+1)+"/"+str(tool_checks)+" | "+bcolors.OKBLUE+tool_names[tool][arg2]+bcolors.ENDC,
            if tool_names[tool][arg4] == 0:
                print bcolors.WARNING+"...Scanning Tool Unavailable. Auto-Skipping Test..."+bcolors.ENDC
                rs_skipped_checks = rs_skipped_checks + 1
                tool = tool + 1
                continue
            spinner.start()
            scan_start = time.time()
            temp_file = "temp_"+tool_names[tool][arg1]
            cmd = tool_cmd[tool][arg1]+target + \
                tool_cmd[tool][arg2]+" > "+temp_file+" 2>&1"

            try:
                subprocess.check_output(cmd, shell=True)
            except KeyboardInterrupt:
                runTest = 0
            except:
                runTest = 1

            if runTest == 1:
                spinner.stop()
                scan_stop = time.time()
                elapsed = scan_stop - scan_start
                rs_total_elapsed = rs_total_elapsed + elapsed
                print bcolors.OKBLUE+"\b...Completed in " + \
                    display_time(int(elapsed))+bcolors.ENDC+"\n"
                clear()
                rs_tool_output_file = open(temp_file).read()
                if tool_status[tool][arg2] == 0:
                    if tool_status[tool][arg1].lower() in rs_tool_output_file.lower():
                        #print "\t"+ vul_info(tool_resp[tool][arg2]) + bcolors.BADFAIL +" "+ tool_resp[tool][arg1] + bcolors.ENDC
                        vul_remed_info(
                            tool, tool_resp[tool][arg2], tool_resp[tool][arg3])
                        rs_vul_list.append(
                            tool_names[tool][arg1]+"*"+tool_names[tool][arg2])
                else:
                    if any(i in rs_tool_output_file for i in tool_status[tool][arg6]):
                        m = 1  # This does nothing.
                    else:
                        #print "\t"+ vul_info(tool_resp[tool][arg2]) + bcolors.BADFAIL +" "+ tool_resp[tool][arg1] + bcolors.ENDC
                        vul_remed_info(
                            tool, tool_resp[tool][arg2], tool_resp[tool][arg3])
                        rs_vul_list.append(
                            tool_names[tool][arg1]+"*"+tool_names[tool][arg2])
            else:
                runTest = 1
                spinner.stop()
                scan_stop = time.time()
                elapsed = scan_stop - scan_start
                rs_total_elapsed = rs_total_elapsed + elapsed
                print bcolors.OKBLUE+"\b\b\b\b...Interrupted in " + \
                    display_time(int(elapsed))+bcolors.ENDC+"\n"
                clear()
                print "\t"+bcolors.WARNING + \
                    "Test Skipped. Performing Next. Press Ctrl+Z to Quit RapidScan." + bcolors.ENDC
                rs_skipped_checks = rs_skipped_checks + 1

            tool = tool+1

        print bcolors.BG_ENDL_TXT + \
            "[ Preliminary Scan Phase Completed. ]"+bcolors.ENDC
        print "\n"

 #################### Report & Documentation Phase ###########################
        print bcolors.BG_HEAD_TXT + \
            "[ Report Generation Phase Initiated. ]"+bcolors.ENDC
        if len(rs_vul_list) == 0:
            print "\t"+bcolors.OKGREEN+"No Vulnerabilities Detected."+bcolors.ENDC
        else:
            with open("RS-Vulnerability-Report", "a") as report:
                while(rs_vul < len(rs_vul_list)):
                    vuln_info = rs_vul_list[rs_vul].split('*')
                    report.write(vuln_info[arg2])
                    report.write("\n------------------------\n\n")
                    temp_report_name = "temp_"+vuln_info[arg1]
                    with open(temp_report_name, 'r') as temp_report:
                        data = temp_report.read()
                        report.write(data)
                        report.write("\n\n")
                    temp_report.close()
                    rs_vul = rs_vul + 1

                print "\tComplete Vulnerability Report for "+bcolors.OKBLUE+target+bcolors.ENDC+" named "+bcolors.OKGREEN + \
                    "`RS-Vulnerability-Report`"+bcolors.ENDC + \
                    " is available under the same directory RapidScan resides."

            report.close()
        # Writing all scan files output into RS-Debug-ScanLog for debugging purposes.
        for file_index, file_name in enumerate(tool_names):
            with open("RS-Debug-ScanLog", "a") as report:
                try:
                    with open("temp_"+file_name[arg1], 'r') as temp_report:
                        data = temp_report.read()
                        report.write(file_name[arg2])
                        report.write("\n------------------------\n\n")
                        report.write(data)
                        report.write("\n\n")
                    temp_report.close()
                except:
                    break
            report.close()

        print "\tTotal Number of Vulnerability Checks        : " + \
            bcolors.BOLD+bcolors.OKGREEN+str(len(tool_names))+bcolors.ENDC
        print "\tTotal Number of Vulnerability Checks Skipped: " + \
            bcolors.BOLD+bcolors.WARNING+str(rs_skipped_checks)+bcolors.ENDC
        print "\tTotal Number of Vulnerabilities Detected    : " + \
            bcolors.BOLD+bcolors.BADFAIL+str(len(rs_vul_list))+bcolors.ENDC
        print "\tTotal Time Elapsed for the Scan             : "+bcolors.BOLD + \
            bcolors.OKBLUE+display_time(int(rs_total_elapsed))+bcolors.ENDC
        print "\n"
        print "\tFor Debugging Purposes, You can view the complete output generated by all the tools named " + \
            bcolors.OKBLUE+"`RS-Debug-ScanLog`"+bcolors.ENDC+" under the same directory."
        print bcolors.BG_ENDL_TXT + \
            "[ Report Generation Phase Completed. ]"+bcolors.ENDC

        os.system('setterm -cursor on')
        os.system('rm te* > /dev/null 2>&1')  # Clearing previous scan files
