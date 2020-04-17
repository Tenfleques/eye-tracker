using System;  
using System.Net;  
using System.Net.Sockets;  
using System.Text;  
  
public class SocketClient  
{  
    Socket sender;
    IPEndPoint remoteEP;

    public SocketClient(Int port = 11000){
        byte[] bytes = new byte[1024];  
  
        try  
        {  
            IPHostEntry host = Dns.GetHostEntry("localhost");  
            IPAddress ipAddress = host.AddressList[0];  
            remoteEP = new IPEndPoint(ipAddress, port);  
  
            // Create a TCP/IP  socket.
            sender = new Socket(ipAddress.AddressFamily,  
                SocketType.Stream, ProtocolType.Tcp);   
        }  
        catch (Exception e)  
        {  
            Console.WriteLine(e.ToString());  
        }  
    }
    public static void CloseClient(){
        // Release the socket.  
        if (sender){
            sender.Shutdown(SocketShutdown.Both);  
            sender.Close();  
        }
    }
    public static void SendMessage(String message){
        // Connect the socket to the remote endpoint. Catch any errors.    
            try{  
                // Connect to Remote EndPoint  
                sender.Connect(remoteEP);  
  
                Console.WriteLine("Socket connected to {0}",  
                    sender.RemoteEndPoint.ToString());  
  
                // Encode the data string into a byte array.    
                byte[] msg = Encoding.ASCII.GetBytes(message);  
  
                // Send the data through the socket.    
                int bytesSent = sender.Send(msg);
  
            } 
            catch (ArgumentNullException ane){  
                Console.WriteLine("ArgumentNullException : {0}", ane.ToString());  
            }  
            catch (SocketException se){  
                Console.WriteLine("SocketException : {0}", se.ToString());  
            }  
            catch (Exception e){  
                Console.WriteLine("Unexpected exception : {0}", e.ToString());  
            }  
    }
}  

namespace TEyeStreams
{
    class Program
    {
        static void Main(string[] args)
        {
            // create the interaction library
            IL.IInteractionLib intlib = IL.InteractionLibFactory.CreateInteractionLib(IL.FieldOfUse.Interactive);

            // create the socket client
            SocketClient socketClient = SocketClient();

            // Screen.PrimaryScreen.Bounds.Width and Screen.PrimaryScreen.Bounds.Height
            const float width  = Screen.PrimaryScreen.Bounds.Width;
            const float height = Screen.PrimaryScreen.Bounds.Height;
            const float offset = 0.0f;
            
            intlib.CoordinateTransformAddOrUpdateDisplayArea(width, height);
            intlib.CoordinateTransformSetOriginOffset(offset, offset);

            // subscribe to gaze point data; print data to console when called
            intlib.GazePointDataEvent += evt =>
            {
                String msg = "x: " + evt.x
                    + ", y: " + evt.y
                    + ", validity: " + (evt.validity == IL.Validity.Valid ? "valid" : "invalid")
                    + ", timestamp: " + evt.timestamp_us + " us";

                Console.WriteLine(msg);
                socketClient.SendMessage(msg);
            };

            Console.WriteLine("Starting interaction library update loop.");
            // setup and maintain device connection, wait for device data between events and 
            // update interaction library to trigger all callbacks, stop after 200 cycles
            const int max_cycles = 500;
            var cycle = 0;
            while (cycle++ < max_cycles)
            {
                intlib.WaitAndUpdate();
            }

            // close seocket connection 
            socketClient.CloseClient();
        }
    }
}
