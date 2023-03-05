#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>
#include <pcap/pcap.h> 

#include <iostream>
#include <vector>
#include <map>

#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/ether.h> 

#include <linux/ip.h>
#include <linux/udp.h>
#include <linux/tcp.h>
#include <linux/icmp.h>

#define DEBUG 0

using namespace std;

struct option long_options[] = {
    {"interface", required_argument, nullptr, 'i'},
    {"count", required_argument, nullptr, 'c'},
    {"filter", required_argument, nullptr, 'f'},
    {"help", no_argument, nullptr, 'h'},
    {nullptr, 0, nullptr, 0}
};

char errbuf[PCAP_ERRBUF_SIZE];

void packet_capturer(string interface, int count, string filter){
    struct bpf_program fp; // for filter, compiled in "pcap_compile"
    pcap_t *handle;
    handle = pcap_open_live({interface.c_str()}, 65535, 1, 1, errbuf);  
    //pcap_open_live(device, snaplen, promise, to_ms, errbuf), interface is your interface, type is "char *"   

    if(!handle || handle == NULL){
        fprintf(stderr, "pcap_open_live(): %s\n", errbuf);
        exit(1);
    }

    if(-1 == pcap_compile(handle, &fp, {filter.c_str()}, 1, PCAP_NETMASK_UNKNOWN) ){ // compile "your filter" into a filter program, type of {your_filter} is "char *"
        pcap_perror(handle, "pkg_compile compile error\n");
        exit(1);
    }

    if(-1 == pcap_setfilter(handle, &fp)){ // make it work
        pcap_perror(handle, "set filter error\n");
        exit(1);
    }

    for(int num = 0; count < 0 || num < count; num++){
        cout << '\n';
#if DEBUG
        cout << num << '\t' << count << '\n';
#endif
        struct pcap_pkthdr header;
        const unsigned char* packet = pcap_next(handle, &header);
        struct ether_header *eptr = (struct ether_header *) packet;
        const int packet_len = header.len;
        const int ether_len = sizeof(ether_header);
#if DEBUG
        cout << "Packert length: " << packet_len << '\n';
        cout << "Ethernet header length: " << ether_len << '\n';
        cout << "Source MAC: "<< ether_ntoa((const struct ether_addr *)&eptr->ether_shost) << '\n';
        cout << "Destination MAC: "<< ether_ntoa((const struct ether_addr *)&eptr->ether_dhost) << '\n';
        printf("Ethertype: 0x%04x\n", ntohs(eptr->ether_type));
#endif
        if(ntohs(eptr->ether_type) != ETHERTYPE_IP){
#if DEBUG
            cout << "Not IP packet\n";
#endif
            continue;
        }

        struct iphdr *ip = (struct iphdr *) (packet + sizeof(ether_header));
        const int ip_len = ip->ihl * 4;
#if DEBUG
        cout << "IP header length: " << ip_len << '\n';
#endif
        if(ip->version != 4){
#if DEBUG
            cout << "Not IPv4\n";
#endif
            continue;
        }

        if(ip->protocol == IPPROTO_TCP){
            struct tcphdr *tcp = (struct tcphdr *) (packet + ether_len + ip_len);
            const int tcp_len = tcp->doff * 4;
#if DEBUG
            cout << "TCP header length: " << tcp_len << '\n';
#endif
            cout << "Transport type: TCP\n";
            cout << "Source IP: " << inet_ntoa(*(struct in_addr *)&ip->saddr) << '\n';
            cout << "Destination IP: " << inet_ntoa(*(struct in_addr *)&ip->daddr) << '\n';
            cout << "Source port: " << ntohs(tcp->source) << '\n';
            cout << "Destination port: " << ntohs(tcp->dest) << '\n';
            cout << "Payload:";
            int len = ether_len + ip_len + tcp_len;
            for(int i = len; i < len + 16 && i < packet_len; i++) printf(" %02x", packet[i]);
            cout << '\n';

        }else if(ip->protocol == IPPROTO_UDP){
            struct udphdr *udp = (struct udphdr *) (packet + ether_len + ip_len);
            const int udp_len = sizeof(udphdr);
#if DEBUG
            cout << "UDP header length: " << udp_len << '\n';
#endif
            cout << "Transport type: UDP\n";
            cout << "Source IP: " << inet_ntoa(*(struct in_addr *)&ip->saddr) << '\n';
            cout << "Destination IP: " << inet_ntoa(*(struct in_addr *)&ip->daddr) << '\n';
            cout << "Source port: " << ntohs(udp->source) << '\n';
            cout << "Destination port: " << ntohs(udp->dest) << '\n';
            cout << "Payload:";
            int len = ether_len + ip_len + udp_len;
            for(int i = len; i < len + 16 && i < packet_len; i++) printf(" %02x", packet[i]);
            cout << '\n';

        }else if(ip->protocol == IPPROTO_ICMP){
            struct icmphdr *icmp = (struct icmphdr *) (packet + ether_len + ip_len);
            const int icmp_len = sizeof(icmphdr);
#if DEBUG
            cout << "ICMP header length: " << icmp_len << '\n';
#endif
            cout << "Transport type: ICMP\n";
            cout << "Source IP: " << inet_ntoa(*(struct in_addr *)&ip->saddr) << '\n';
            cout << "Destination IP: " << inet_ntoa(*(struct in_addr *)&ip->daddr) << '\n';
            cout << "ICMP type value: " << uint(icmp->type) << '\n';
            
        }else{
            cout << "Not TCP or UDP or ICMP\n";
            continue;
        }

    }

}

int main(int argc, char*argv[]){
    int opt, count = -1;
    string interface = "", filter = "all";

    while ((opt = getopt_long(argc, argv, "i:c:f:h", long_options, nullptr)) != -1) {
        switch (opt) {
            case 'i':
                interface = optarg;
                break;
            case 'c':
                try{
                    count = stoi(optarg);
                }catch(exception &e){
                    cerr << "Error -c {number}: " << e.what() << '\n';
                    return 1;
                }
                break;
            case 'f':
                filter = optarg;
                break;
            case 'h':
                cout << "Usage: \n";
                cout << "--interface {interface}, -i {interface}\n";
                cout << "--count {number}, -c {number}\n";
                cout << "--filter {udp, tcp, icmp, all}, -f {udp, tcp, icmp, all}\n";
                return 0;
            default:
                //cerr << "Unknown argument: [" << opt << "].\n";
                return 1;
        }
    }

#if DEBUG
    cout << "Argument value:\n";
    cout << "Interface: " << interface << "\n";
    cout << "Count: " << count << "\n";
    cout << "Filter: " << filter << "\n";
#endif

    if(interface == ""){
        cerr << "Error: This error is caused because you did not specify the interface when running your program.\n";
        return 1;
    }

    //get all devices 
    pcap_if_t *devices = NULL;
    if(-1 == pcap_findalldevs(&devices, errbuf)) {
        cerr << "pcap_findalldevs: " << errbuf << "\n";// if error, fprint error message --> errbuf
        exit(1);
    }

    bool foundInterface = false;
    for(pcap_if_t *d = devices; d ; d = d->next){
#if 0
        cout << "Name: " << d->name << '\n';
#endif
        if(interface == string(d->name)){
            foundInterface = true;
        }
    }

    if(!foundInterface){
        cerr << "Interface [" << interface << "] is not exists.\n";
        return 1;
    }
    
    if(filter != "udp" && filter != "tcp" && filter != "icmp" && filter != "all"){
        cerr << "Filter [" << filter << "] is illegal.\n";
        return 1;
    }

    if(filter == "all"){
        filter = "ip";
    }

    packet_capturer(interface, count, filter);

    pcap_freealldevs(devices);

    return 0;
}