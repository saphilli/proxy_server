import socket,sys,_thread#import modules

buffer_size = 4096
max_connections = 5
blacklist = "blacklist.txt"



def start_proxy():
    print("Welcome to the proxy server!")
    listen_port = int(input("Please enter an available port number: "))

    #block option
    do_block = str(input("Add to blacklist of urls? (Y/N): "))
    if(do_block == "Y"):
        while True:
            to_block = str(input("Enter the url that you want the proxy to block or enter 'skip' to skip: (Note - don't include ://') "))
            if to_block == "skip":
                break
            bl_file = open(blacklist,"a+")
            bl_file.write(to_block +"\n")
            bl_file.close()
    #unblock option
    do_unblock = str(input("Remove urls from blacklist? (Y/N): "))
    if(do_unblock == "Y"):
        while True:
            to_unblock = str(input("Enter the url that you want the proxy to unblock or enter 'skip' to skip: (Note - don't include ://') "))
            if to_unblock == "skip":
                break
            bl_file = open(blacklist,'r')
            lines = bl_file.readlines()
            bl_file.close()
            bl_file = open(blacklist,'w')
            for l in lines:
                if l != to_unblock+"\n":
                    bl_file.write(l)
            bl_file.close()
    #make instance of socket
    #SOCK_STREAM refers to the TCP protocol, AF_INET refers to ipv4
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        print("Socket created")
        #bind to port, put host field as empty in order to get the server to listen for request
        s.bind(('',listen_port))
        s.listen(max_connections)
        print("Socket binded to " +str(listen_port))
        print("Proxy server has been activated")
    except KeyboardInterrupt:
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)
    except Exception as e:
        print("Socket creation failed due to an error: \n"+ str(e))
        sys.exit(2)
    #infinite loop until error occurs, or it is interrupted
    while True:
        try:
            browser,addr = s.accept() #accept incoming connection,
            #browser is a new socket object used to send+receive data on connection
            #address is the address bound to the socket on the other end
            print("Connection established with " +str(addr))
            req_message = browser.recv(buffer_size) #receive the payload (data) from client
            _thread.start_new_thread(handle_request,(browser,req_message,addr)) #start a new thread
        except KeyboardInterrupt:
            s.close()
            print("\n[*] Shutting down the proxy server...")
            print("\n[*] Successfully shut down")
            sys.exit(1)
    s.close()


def parse_request(message):
    try:
        decoded_message = message.decode('utf-8')   #convert to utf-8
        first_line = decoded_message.split('\n')[0]       #remove empty line
        print(first_line)                                 #for debugging purposes
        url = first_line.split(' ')[1] #remove GET/CONNECT at start
        url_pos= url.find("://") #find position of the :// in the string
        protocol = url[:url_pos] #protocol = http or https
        if(url_pos==-1): #if :// not found
            tmp = url
        else:
            tmp = url[(url_pos+3):] #get url (after ://)
        port_pos= tmp.find(":") #locate the port number (comes after :)
        host_pos = tmp.find("/") #comes after / after the port number
        if host_pos == -1 : #if / not found
            host_pos= len(tmp) #put index of host as end of string
        host = "" #declare host
        port = -1 #declare port variable

        if (port_pos ==-1 or host_pos < port_pos): #if : not present or the index of / is before :
            port = 80 #default to common HTTP port
            host = tmp[:host_pos] #get host from string
        else:
            port= int((tmp[(port_pos+1):])[:host_pos-port_pos-1]) #isolate specific port
            host = tmp[:port_pos]
        return {
            "message": message,
            "method": first_line.split(' ')[0], #GET/CONNECT
            "port" :port,
            "host" :host,
            "url"  :url,
            "protocol" :protocol,
        }
    except KeyboardInterrupt:
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)
    except Exception as e:
        pass

def is_blocked(host):
    bl = open(blacklist,'r')
    lines = bl.readlines()
    for l in lines:
        if l.find(host) != -1:
            bl.close()
            return True
    bl.close()
    return False

def handle_request(browser,message,addr):
    try:
        parsed_message = parse_request(message)
        is_url_blocked = is_blocked(parsed_message["host"])
        host = parsed_message["host"]
        port = parsed_message["port"]
        if (is_url_blocked == True):
            print("**The url that was requested: "+host+ " has been blocked :(\n")
        else:
            if port == 443: #HTTPS common port 443
                https_tunnel(host,port,browser,addr,message)
            else:
                http_request(host,port,browser,addr,message)
    except KeyboardInterrupt:
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)
    except Exception as e:
    #    print("Error occurred while directing the request: "+ str(e))
        pass


def https_tunnel(host,port,browser,addr,message):
    try:
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect((host,port))
        reply = "HTTP/1.0 200 Connection established\r\nProxy-agent: Pyx\r\n\r\n"
        browser.sendall(reply.encode()) #
        browser.setblocking(0)
        client.setblocking(0)
    except KeyboardInterrupt:
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)
    except Exception as e:
        print("Error occurred"+ str(e))

    while True:
        try:
            request = browser.recv(1024)
            client.send(request)
        except Exception as e:
            pass
        try:
            reply = client.recv(1024)
            if(len(reply)<1):
                break
            browser.send(reply)
        except Exception as e:
            pass
    print("Https Request completed ")
    client.close() #close sockets
    browser.close()

def http_request(host,port,browser,addr,message):
    try:
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((host,port))
        s.sendall(message)
        while True:
            reply = s.recv(buffer_size)
            if(len(reply) > 0): #if the reply string is nonempty
                browser.send(reply) #send a http reply to the client
                print("Http Request completed")
            else:
                break
        s.close()
        browser.close()
    except KeyboardInterrupt:
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)
    except Exception as e:
        s.close()
        browser.close()
        sys.exit(1)

start_proxy()
