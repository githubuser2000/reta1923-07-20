import sys

import reta

retaProgram = reta.Program([sys.argv[0]])
mainParas = ["-" + a for a in retaProgram.mainParaCmds]
# print(str(mainParas))
# print(str(retaProgram.paraDict))
spalten = ["--" + a[0] for a in retaProgram.paraDict.keys()]
# print(str(list(spalten)))
# print(str(reta.Program.kombiParaNdataMatrix.values()))
# print(str(reta.Program.kombiParaNdataMatrix2.values()))
#
#
# DAS SOLLTE ICH BESSER ALLES ORDENTLICH IN RETA.PY PACKEN, STATT ES HIER AUSZUSCHREIBEN, WEIL SONST DOPPELT!
# D.H. spezielle DatenTypen dafür in Reta.py anlegen!
# DAS GEHT SCHNELL, FLEIßARBEIT, WEIL KAUM BUGGEFAHR
#
# startpunkt: dict = {}
spaltenDict = {}
for tupel in retaProgram.paraNdataMatrix:
    for haupt in tupel[0]:
        spaltenDict[haupt] = tupel[1]
# pp(spaltenDict)

ausgabeParas = [
    "--nocolor",
    "--art",
    "--onetable",
    "--spaltenreihenfolgeundnurdiese",
]
kombiMainParas = ["--galaxie", "--universum"]
zeilenParas = [
    "--zeit",
    "--zaehlung",
    "--vorhervonausschnitt",
    "--primzahlvielfache",
    "--nachtraeglichdavon",
    "--alles",
    "--potenzenvonzahlen",
    "--typ",
]
hauptForNeben = ("-zeilen", "-spalten", "-kombination", "-ausgabe")
