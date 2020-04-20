using System;
using System.Net;
using System.Net.Sockets;
using System.Text;

namespace EyeStreams
{
    class Program
    {
        static Socket listener;
        static Socket handler;

        private static void InitClient(int port = 11000)
        {
            // Get Host IP Address that is used to establish a connection  
            // In this case, we get one IP address of localhost that is IP : 127.0.0.1  
            // If a host has multiple addresses, you will get a list of addresses  

            IPHostEntry host = Dns.GetHostEntry("localhost");
            IPAddress ipAddress = host.AddressList[0];
            IPEndPoint localEndPoint = new IPEndPoint(ipAddress, port);
            try
            {
                
                listener = new Socket(ipAddress.AddressFamily, SocketType.Stream, ProtocolType.Tcp);

                listener.Bind(localEndPoint);
                // Specify how many requests a Socket can listen before it gives Server busy response.  
                // We will listen 10 requests at a time  
                listener.Listen(10);

                Console.WriteLine("Waiting for a connection...");
            }
            catch (ArgumentNullException ane)
            {
                Console.WriteLine("ArgumentNullException : {0}", ane.ToString());
            }
            catch (SocketException se)
            {
                Console.WriteLine("SocketException : {0}", se.ToString());
            }
            catch (Exception e)
            {
                Console.WriteLine("Unexpected exception : {0}", e.ToString());
            }
        }

        private static void InitSender()
        {
            try
            {
                Console.WriteLine("Waiting for a new connection...");
                handler = listener.Accept();

                // Incoming data from the client.    
                string data = null;
                byte[] bytes = null;

                while (true)
                {
                    bytes = new byte[1024];
                    int bytesRec = handler.Receive(bytes);
                    data += Encoding.ASCII.GetString(bytes, 0, bytesRec);
                    Console.WriteLine("connected : {0}", data);

                    if (data.IndexOf("stream") > -1)
                    {
                        break;
                    }
                }
            }
            catch (ArgumentNullException ane)
            {
                Console.WriteLine("ArgumentNullException : {0}", ane.ToString());
            }
            catch (SocketException se)
            {
                Console.WriteLine("SocketException : {0}", se.ToString());
            }
            catch (Exception e)
            {
                Console.WriteLine("Unexpected exception : {0}", e.ToString());
            }


        }
        private static void SendMessage(String message)
        {
            try
            {
                // Encode the data string into a byte array.    
                byte[] msg = Encoding.ASCII.GetBytes(message);

                // Send the data through the socket. 
                int bytesSent = handler.Send(msg);
            }
            catch (Exception e)
            {
                Console.WriteLine("error: {0}", e.ToString());
            }
        }

        public static void CloseClient()
        {
            // Release the socket.  
            if (handler.Connected)
            {
                handler.Shutdown(SocketShutdown.Both);
                handler.Close();
            }
            else
            {
                listener.Close();
            }
        }

        static void Main(string[] args)
        {
            // create the interaction library
            IL.IInteractionLib intlib = IL.InteractionLibFactory.CreateInteractionLib(IL.FieldOfUse.Interactive);

            // assume single screen with size 2560x1440 and use full screen (not window local) coordinates
            const float width = 2560.0f;
            const float height = 1440.0f;
            const float offset = 0.0f;

            intlib.CoordinateTransformAddOrUpdateDisplayArea(width, height);
            intlib.CoordinateTransformSetOriginOffset(offset, offset);

            InitClient();

            // subscribe to gaze point data; print data to console when called
            intlib.GazePointDataEvent += evt =>
            {
                String msg = "x: " + evt.x
                    + ", y: " + evt.y
                    + ", validity: " + (evt.validity == IL.Validity.Valid ? "valid" : "invalid")
                    + ", timestamp: " + evt.timestamp_us + " us";

                if (handler.Connected)
                {
                    SendMessage(msg);
                    Console.WriteLine(msg);
                }

            };

            Console.CancelKeyPress += delegate {
                CloseClient();
                Environment.Exit(0);
            };
            while (true)
            {
                InitSender();
                Console.WriteLine("Starting interaction library update loop.");
                while (handler.Connected)
                {
                    intlib.WaitAndUpdate();
                }
                handler.Close();
                Console.WriteLine("connection down.");
            }

            
        }
    }
}
