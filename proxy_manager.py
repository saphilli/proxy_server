import proxy, threading,time,sys



def background():
    print("The following commands can be entered to carry out various actions:\n")
    print("Enter 'block' to add a URL to the blacklist.\n")
    print("Enter 'unblock' to remove a URL from the blacklist.\n")
    print("Enter 'stop' to stop the proxy server.")
    while True:
        if (input() == 'stop'):
            print("Shutting down proxy....")
            sys.exit(0)




thread1 = threading.Thread(target=background)
thread1.daemon = True
thread1.start()
proxy.start_proxy()


import time,datetime,os,json,socket,sys,_thread#import modules

buffer_size = 4096
max_connections = 5
blacklisted = []
blacklist = "blacklist.txt"
blocked = []


def start_proxy():
    print("Welcome to the proxy server!")
    listen_port = int(input("Please enter an available port number: "))

    bl_file = open(blacklist,"w+")
    data = ""
    while True:
        line = bl_file.read()
        if not len(line):
            break
        data += line
        f.close()
        blocked = data.splitlines()
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
    except Exception as e:
        print("Socket creation failed due to an error: \n"+ str(e))
        sys.exit(2)
    except KeyboardInterrupt:
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)

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

def is_blocked(browser, addr,parsed_message):
    if not (parsed_message["url"] + ":" + str(parsed_message["port"])) in blocked:
        return False
    return True

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
    except Exception as e:
        print("Error occurred while parsing the message: "+ str(e))
    except KeyboardInterrupt:
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)

def handle_request(browser,message,addr):
    try:
        parsed_message = parse_request(message)
        block_status = is_blocked(browser,addr, parsed_message) #true = blocked
        if block_status == True:
            print("The requested URL is blocked")
            browser.send("ERROR")

        host = parsed_message["host"]
        port = parsed_message["port"]
        if port  == 443: #HTTPS common port 443
            https_tunnel(host,port,browser,addr,parsed_message)
        else:
            http_request(host,port,browser,addr,parsed_message)
    except Exception as e:
        print("Error occurred while directing the request: "+ str(e))
    except KeyboardInterrupt:
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)


def https_tunnel(host,port,browser,addr,parsed_message):
    try:
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect((host,port))
        reply = "HTTP/1.0 200 Connection established\r\nProxy-agent: Pyx\r\n\r\n"
        browser.sendall(reply.encode()) #
        browser.setblocking(0)
        client.setblocking(0)
    except Exception as e:
        print("Error occurred"+ str(e))
    except KeyboardInterrupt: #allow user to ctrl+c
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)

    while True:
        try:
            request = browser.recv(1024)
            client.send(request)
        except Exception as e:
            #print("Error occurred while sending request: "+ str(e))
            pass
        try:
            reply = client.recv(1024)
            if(len(reply)<1):
                break
            browser.send(reply)
        except Exception as e:
            #print("Error occurred while sending reply: "+ str(e))
            pass
    print("Https Request completed")
    client.close() #close sockets
    browser.close()

def http_request(host,port,browser,addr,parsed_message):
    try:
        request = parsed_message["message"]
        url = parsed_message["url"]
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((host,port))
        s.sendall(request)
        cachedFile = open(filename,'wb+')
        while True:
            reply = s.recv(buffer_size)
            if(len(reply) > 0): #if the reply string is nonempty
                cachedFile.write(reply)
                browser.send(reply) #send a http reply to the client
                tmp=float(len(reply))
                tmp = float(tmp/1024)
                tmp = "%.3s" % (str(tmp))
                tmp = "%s KB" % (tmp)
                print("Http Request completed:"+ str(addr[0]),str(tmp))
            else:
                    break
            s.close()
            browser.close()
    except Exception as e:
        s.close()
        browser.close()
        sys.exit(1)
    except KeyboardInterrupt:
        s.close()
        print("\n[*] Shutting down the proxy server...")
        print("\n[*] Successfully shut down")
        sys.exit(1)

def cache(reply, browser):
    while True:
        try:
            if(len(reply)<1):
                break
            browser.send(reply)
        except socket.error as e;
            pass
        browser.close()

def check_cache(filename):
    print("checking cache")
    try:
        f = open(filename,"rb")
        cacheData = f.read()
        f.close()
    except Exception as e:
        cacheData = None
    if(cacheData != None):
        print("Cache hit")
        return cacheData
    else:
        print("Cache miss")
        return None


start_proxy
