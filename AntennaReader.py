from serial import Serial
from numpy import savetxt, fromstring, append, float64
from time import sleep
from math import log
import socket

CH340 = Serial("COM" + input("Insert COM port number: "), baudrate=115200)
sleep(1)
file_1 = 'A_OFFSET.csv PATH'
file_2 = 'A_DATA.csv PATH'
OFFSET_Data = []

HOST = '127.0.0.1'
PORT = 65432

while True:
    Data_Row = (CH340.readline()).decode('latin_1')
    if not "][E][" in Data_Row:
        Data_Row = Data_Row.replace("\n", "")
        print(Data_Row)
    if "Sensors are good" in Data_Row:
        print("0")
    if "Starting Calibration, keep sensor still" in Data_Row:
        print("1")
        break


while True:
    Data_Row = (CH340.readline()).decode('latin_1')
    Data_Row = Data_Row.replace("\n", "")
    print(Data_Row)
    Data_Row = Data_Row.replace("\r", "")
    if "," in Data_Row:
        OFFSET_Data = append(arr=OFFSET_Data, values=Data_Row)
    if "Calibration Completed" in Data_Row:
        print("2")
        break

savetxt(fname=file_1, X=OFFSET_Data, delimiter=',', fmt='%s')



with open(file_2, 'at') as f:
    while True:
        Data_Row = (CH340.readline()).decode('latin_1')
        Data_Row = Data_Row.replace("\n", "")
        print(Data_Row)
        Data_Row = Data_Row.replace("\r", "")
        if "_" in Data_Row:
            savetxt(fname=f, X=[Data_Row], delimiter=',', fmt='%s' )
        elif "," in Data_Row:
            savetxt(fname=f, X=[Data_Row], delimiter=",", fmt='%s')
            D = fromstring(string=Data_Row, sep=',')
            P_DATA = [D[0], D[1], D[2], D[3], D[4], D[5], D[16], D[15], D[17], D[13], D[14], 100*(log(D[15])/(log(0.9877)))]
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    Data = [float(x) if isinstance(x, float64) else x for x in Data] #converte tutti i valori in float64 di numpy (valori vettoriali)
                    s.connect((HOST, PORT)) #tenta la connessione al server
                    s.sendall(str(Data).encode('utf-8'))  #codifica i dati in utf-8 e li manda al server
            except ConnectionRefusedError:
                print("Errore: impossibile connettersi al server CSVReader.")   #se la connessione fallisce manda un messaggio di errore



print("done")
