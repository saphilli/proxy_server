import socket,sys,_thread#import modules

buffer_size = 4096 #max buffer size of Socket
max_connections = 5 #max amount of connections to the proxy server
blacklisted = []
blacklist = "blacklist.txt"
cache_path = "./cache"
#listen_port=8001 #hardcode port 8001 for now
def main():
    print("Welcome to the proxy server!")
    listen_port = int(input("Please enter an available port number: "))
    
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM) #make instance of socket
    #SOCK_STREAM refers to the TCP protocol, AF_INET refers to ipv4
        print("Socket created")
        #bind to port, put IP field as empty in order to get the server to listen for requests
        s.bind(('',listen_port)) #bind to port 8001
        s.listen(max_connections)
        print("Socket binded to " +str(listen_port))
        print("Proxy server running successfully")
    except Exception as e:
        print("Socket creation failed due to an error: \n"+ str(e)) #catch errors and print
        sys.exit(2)

    #infinite loop until error occurs, or it is interrupted
    while True:
        try:
            browser,addr = s.accept() #accept incoming connection,
            #conn is a new socket object used to send+receive data on connection
            #address is the address bound to the socket on the other end
            print("Connection established with " +str(addr))
            req_message = browser.recv(buffer_size) #receive the payload (data) from client
            _thread.start_new_thread(request_message,(browser,req_message,addr)) #start a new thread
        except KeyboardInterrupt: #allow user to ctrl+c
            s.close()
            print("\n[*] Shutting down the proxy server...")
            print("\n[*] Successfully shut down")
            sys.exit(1)
    s.close()

def request_message(browser,message,addr):
    try:
        decoded_message = message.decode('utf-8') #convert to utf-8
        data = decoded_message.split('\n')[0]#remove empty line
        print(data) #for debugging purposes
        url = data.split(' ')[1] #remove GET/CONNECT at start
        http_pos= url.find("://") #find position of the :// in the string
        if(http_pos==-1): #if :// not found
            tmp = url #assign the data to tmp variable
        else:
            tmp = url[(http_pos+3):] #get url (after ://)
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

        if port == 443:
            # HTTPS common port 443
            https_tunnel(host,port,browser,addr,message)
        else:
            http_request(host,port,browser,addr,message)
    except Exception as e:
        print("Error occurred"+ str(e))



def https_tunnel(host,port,browser,addr,payload):
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

def http_request(host,port,browser,addr,payload):
    try:
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((host,port))
        s.sendall(payload)
        while True:
            reply = s.recv(buffer_size)

            if(len(reply) > 0): #if the reply string is nonempty
                browser.send(reply) #send a http reply to the client
                tmp=float(len(reply))
                tmp = float(tmp/1024)
                tmp = "%.3s" % (str(tmp))
                tmp = "%s KB" % (tmp)
                'Print a Custom Message for Request Complete'
                print("Http Request completed:"+ str(addr[0]),str(tmp))
            else:
                break
        s.close()
        browser.close()
    except Exception as e:
        s.close()
        browser.close()
        sys.exit(1)

main()
