from customtkinter import *
from tkinter import filedialog
from os.path import basename, splitext
import matplotlib.pyplot as plt
import numpy as np
import Giacobbe as gc
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from ast import literal_eval
from queue import Queue
import pyqtgraph as pg
from tkinter import Frame
from pyqtgraph.Qt import QtWidgets

data_queue = Queue()

HOST = '127.0.0.1'
PORT = 65432

fileName = "N/A"
file = ["N/A", "N/A"]
filePath = "N/A"
readFile = ""

win = None
curveAX = None
curveAY = None
curveAZ = None
curveGX = None
curveGY = None
curveGZ = None
curveTemp = None
curvePress = None
curveAlt = None
app = None

#definisce gli array e li svuota da valori precedenti

AccX = []
AccY = []
AccZ = []

GyroX = []
GyroY = []
GyroZ = []

Time = []

PosX = [0]
PosY = [0]
PosZ = [0]

VelX = [0]
VelY = [0]
VelZ = [0]

Pressure = []
Temperature = []
GPSX = []
GPSY = []
altitude = []

Data = []
ServerRunning = True

#crea un server locale su una porta alta e poco trafficata per ricevere i dati dall'antenna
def startServer():
    global ServerRunning

    #crea il server con ip HOST (127.0.0.1[che è l'indirizzo ip univoco dell'host]) e la porta PORT (65432[una porta alta e poco trafficata])
    with socket(AF_INET, SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen() #lo mette in ascolto per ricevere i dati
        print(f"Server in ascolto su {HOST}:{PORT}...")

        #ciclo while del server
        while ServerRunning:    #finché ServerRunning è True il server va se diventa False il server si ferma
            try:
                conn, addr = s.accept() #accetta la connessione da un client (che dovrebbe essere l'antenna che sta mandando i dati)
                with conn:
                    #salva i dati ricevuti dal client in data
                    data = conn.recv(1024)
                    #se non ci sono dati da salvare interrompe la connessione con quel client e ricomincia il ciclo
                    #se non ci sono dati vuol dire che il client connesso non è antenna
                    if not data: 
                        break

                    #i dati sono in bytes, quindi vanno decodificati in una stringa per poter essere letti da noi umani stupidi che non sappiamo leggere i bytes
                    #la stringa è in formato utf-8, quindi la decodifichiamo in utf-8
                    decoded_data = data.decode('utf-8')

                    #in questo try cerchiamo di convertire la stringa in una lista di float, se non ci riusciamo stampiamo l'errore e continuiamo il ciclo
                    #literal_eval è una funzione che converte una stringa in un oggetto python, in questo caso una lista di float
                    try:
                        received_data = literal_eval(decoded_data)
                        if not isinstance(received_data, list):
                            raise ValueError("I dati ricevuti non sono una lista.")
                    except (ValueError, SyntaxError) as e:
                        print(f"Errore durante l'analisi dei dati: {e}")
                        continue

                    #tramite una queue mettiamo i dati ricevuti in una lista per poterli usare in un altro thread (quello del grafico in diretta)
                    #la queue è una struttura dati che permette di mettere in coda i dati e di toglierli in un altro thread senza problemi di concorrenza
                    #il server gira su un thread "secondario" e il grafico in diretta sul thread "principale" e quindi ci scambiamo dati tra un thread e l'altro tramite la queue
                    data_queue.put(received_data)
            except OSError:
                break

#############################################
####           MOMENT GRAPHS             ####
#############################################

#questo è rimasto invariato rispetto alla versione precedente tranne per la modalità interattiva di mpl che viene disattivata (plt.ioff())
def openFileBrowser():
    global filePath
    global fileName
    global file
    global readFile

    global Pressure, Temperature
    global PosX, PosY, PosZ, Time, GyroX, GyroY, GyroZ, AccX, AccY, AccZ, VelX, VelY, VelZ

    print("File browser opened")

    #cerca il file e ne prende le informazioni di base (nome e estensione)
    
    filePath = filedialog.askopenfilename(initialdir = "\\Documents\\")
    fileName = basename(filePath)
    file = splitext(fileName)

    print("\nFile path: " + filePath)
    print("\nFile name: " + file[0])
    print("\nFile type: " + file[1])

    localFile = open(filePath, 'r')
    readFile = localFile.read()

    if file[1] == ".csv" or file[1] == ".CSV":
        array = np.loadtxt(fname=filePath, dtype=float, delimiter=",", skiprows=1)
        GyroX = array[:, 3].astype(float)
        GyroY = array[:, 4].astype(float)
        GyroZ = array[:, 5].astype(float)
        AccX = array[:, 0].astype(float)
        AccY = array[:, 1].astype(float)
        AccZ = array[:, 2].astype(float)
    else:
        dialog = CTkToplevel(root, text = "This is not a .csv file, I can't create any graph with this :(")
        print("Error: the selected file it's not a csv file")

    EData = gc.CSVReader_Class(filePath)

    EData.Calculate()

    filePath = EData.DATA_csv

    localFile = open(filePath, 'r')

    readFile = localFile.read()

    #scrive le informazioni ottenute nel Label FileDatas insieme alla legenda dei grafici

    FileDatas.configure(root, text = ("Name: " + file[0] + "\nFile type: " + file[1] + "\nFile Path: " + filePath))

    localFile.close()

    #prende i dati dal file csv

    if file[1] == ".csv" or file[1] == ".CSV":
        array = np.loadtxt(fname=filePath, dtype=float, delimiter=",", skiprows=1)
        Vel_X = array[:, 3].astype(float)
        Vel_Y = array[:, 4].astype(float)
        Vel_Z = array[:, 5].astype(float)
        PosX = array[:, 6].astype(float)
        PosY = array[:, 7].astype(float)
        PosZ = array[:, 8].astype(float)
        Time = array[:, 9].astype(int)

        """A_X_Gyro = scipy.integrate.cumulative_trapezoid(y=Gyr_X, x=Time)
        A_Y_Gyro = scipy.integrate.cumulative_trapezoid(y=Gyr_Y, x=Time)
        A_Z_Gyro = scipy.integrate.cumulative_trapezoid(y=Gyr_Z, x=Time)"""
    else:
        dialog = CTkToplevel(root, text = "This is not a .csv file, I can't create any graph with this :(")
        print("Error: the selected file it's not a csv file")

    print("done!")

#unica modifica: disattiva la modalità interattiva di matplotlib (plt.ioff())
    plt.ioff()

#grafico dell'accelerazione
    #crea le linee

    plt.plot(Time, AccX, label = "Acceleration X", color = "red")
    plt.plot(Time, AccY, label = "Acceleration Y", color = "green")
    plt.plot(Time, AccZ, label = "Acceleration Z", color = "blue")
    
    #da i nomi al grafico e ai suoi assi

    plt.xlabel('x - Time')
    plt.ylabel('y - Acceleration m/s^2')
    plt.title('Acceleration / Time')
    
    #mostra il grafico
    plt.legend()
    plt.show()

#grafico del giroscopio
    #crea le linee

    plt.plot(Time, GyroX, label = "Gyroscope X", color = "red")
    plt.plot(Time, GyroY, label = "Gyroscope Y", color = "green")
    plt.plot(Time, GyroZ, label = "Gyroscope Z", color = "blue")

    #da i nomi al al grafico e ai suoi assi

    plt.xlabel('x - Time')
    plt.ylabel('y - Gyroscope °/s')
    plt.title('Gyroscope / Time')

    #mostra il grafico

    plt.legend()
    plt.show()

#grafico viaggio
    #prepapra gli assi xyz
    ax = plt.figure().add_subplot(projection='3d')
    ax.plot(PosX, PosY, PosZ, label = 'Traiettoria CanSat in m')
    ax.legend()

    plt.show()

#############################################
####            LIVE GRAPHS              ####
#############################################

#questa parte invece è tutta nuova
def Live_Graph():
    global Pressure, Temperature
    global PosX, PosY, PosZ, Time, GyroX, GyroY, GyroZ, AccX, AccY, AccZ, VelX, VelY, VelZ
    global win, curveAX
    
    if not data_queue.empty():
        Input = data_queue.get()
        Time.append(float(Input[8]) / 1000)
        AccX.append(float(Input[0]))
        AccY.append(float(Input[1]))
        AccZ.append(float(Input[2]))
        GyroX.append(float(Input[3]))
        GyroY.append(float(Input[4]))
        GyroZ.append(float(Input[5]))
        Temperature.append(float(Input[6]))
        Pressure.append(float(Input[7]))
        GPSX.append(float(Input[9]))
        GPSY.append(float(Input[10]))
        altitude.append(float(Input[11]))

        if curveAX is not None:
            curveAX.setData(Time, AccX)
        if curveAY is not None:
            curveAY.setData(Time, AccY)
        if curveAZ is not None:
            curveAZ.setData(Time, AccZ)
        if curveGX is not None: 
            curveGX.setData(Time, GyroX)
        if curveGY is not None:
            curveGY.setData(Time, GyroY)
        if curveGZ is not None:
            curveGZ.setData(Time, GyroZ)
        if curveTemp is not None:
            curveTemp.setData(Time, Temperature)
        if curvePress is not None:
            curvePress.setData(Time, Pressure)
        if curveAlt is not None:
            curveAlt.setData(Time, altitude)

    root.after(1, Live_Graph)

#questa è la funzione che fa partire il server e il grafico in diretta
def StartLG():
    Reset_Variables()
    #roba UI non preoccupatevi (fa comparire il tasto per fermare tutto e fa scomparire quello per farlo partire)
    BLiveGraph.place_forget()
    StopButton.place(relx=0.5, rely=0.2, anchor="center")

    #inizializza il thread del server e lo fa partire
    global ServerRunning
    ServerRunning = True
    server_thread = Thread(target=startServer, daemon=True)
    server_thread.start()

    # Configura PyQtGraph
    global win, curveAX, curveAY, curveAZ, curveGX, curveGY, curveGZ, app, curveTemp, curvePress, curveAlt
    app = pg.mkQApp("Real-Time Plot")
    win = pg.GraphicsLayoutWidget(show=True, title="Real-Time Plot")
    win.resize(1000, 600)

    Aplot = win.addPlot(title="Real-Time Plot Accelerometer")
    curveAX = Aplot.plot(pen='r')
    curveAY = Aplot.plot(pen='g')
    curveAZ = Aplot.plot(pen='b')

    Gplot = win.addPlot(title="Real-Time Plot Gyroscope")
    curveGX = Gplot.plot(pen='r')
    curveGY = Gplot.plot(pen='g')
    curveGZ = Gplot.plot(pen='b')

    Templot = win.addPlot(title="Real-Time Plot Temperature")
    curveTemp = Templot.plot(pen='r')
    
    Pressplot = win.addPlot(title="Real-Time Plot Pression")
    curvePress = Pressplot.plot(pen='y')

    AltitudePlot = win.addPlot(title="Real-Time Plot Altitude")
    curveAlt = AltitudePlot.plot(pen='y')

    # Mostra la finestra PyQtGraph
    win.show()

    Live_Graph()

#questa è la funzione di stop del grafico in diretta
def StopLG():
    global ServerRunning
    ServerRunning = False   #ferma il server
    #roba UI non preoccupatevi (fa comparire il tasto per far partire tutto e fa scomparire quello per fermarlo)
    StopButton.place_forget()
    BLiveGraph.place(relx = 0.5, rely = 0.2, anchor = "center")

def Exit():
    root.quit() #chiude il programma

#resetta le variabili globali per evitare di mettere nei grafici dati che non centrano
def Reset_Variables():
    global Pressure, Temperature
    global PosX, PosY, PosZ, Time, GyroX, GyroY, GyroZ, AccX, AccY, AccZ, VelX, VelY, VelZ

    AccX = []
    AccY = []
    AccZ = []

    GyroX = []
    GyroY = []
    GyroZ = []

    Time = []

    PosX = [0]
    PosY = [0]
    PosZ = [0]

    VelX = [0]
    VelY = [0]
    VelZ = [0]

    Pressure = []
    Temperature = []

#setup di tkinter per creare la UI

#pagina default
root = CTk(className = " CSV Reader Gyromap :)")
set_appearance_mode("dark")
root.geometry("960x540")

#bottone per cercare i file
BrowseButton = CTkButton(root, text = "Insert File", command = openFileBrowser, hover_color = "#5d5dff", text_color = "white" , fg_color = "#0000ff", font = ("Calibri_Light", 20), corner_radius = 24)
BrowseButton.place(relx = 0.5, rely = 0.1, anchor = "center")

#bottone per fermare il grafico in diretta (visibile solo quando i grafici in diretta sono abilitati)
StopButton = CTkButton(root, text = "Stop Live Graph", command = StopLG, text_color = "black", fg_color = "red", hover_color = "#640b0b", font = ("Calibri_Light", 20), corner_radius = 24)
#la parte di place viene fatta solo nello StartLG

#bottone per i grafici in tempo reale
BLiveGraph = CTkButton(root, text = "Start Live Graph", font = ("Calibri_Light", 20), text_color = "black", fg_color = "green", hover_color = "#006400", command = StartLG, corner_radius = 24)
BLiveGraph.place(relx = 0.5, rely = 0.2, anchor = "center")

#bottone per uscire dal programma
ExitButton = CTkButton(root, text = "Exit", command = Exit, text_color = "black", fg_color = "red", hover_color = "#640b0b", font = ("Calibri_Light", 20), corner_radius = 24)
ExitButton.place(relx = 0.1, rely = 0.9, anchor = "center")

#label delle informazioni sul file
FileDatas = CTkLabel(root, text = ("Name: " + file[0] + "\nFile type: " + file[1] + "\nFile Path: " + filePath), justify = "left", fg_color = "transparent", text_color = "white", font = ("Calibri_Light", 20))
FileDatas.place(relx = 0.5, rely = 0.5, anchor = "center")

#avvia la pagina
root.mainloop()
