#!/usr/bin/env pypy3
# -*- coding: utf-8 -*-
import os
import platform
import pprint
import re
import subprocess
import sys
from collections import OrderedDict, defaultdict
from copy import copy, deepcopy
from enum import Enum
from itertools import zip_longest
from typing import Optional

from prompt_toolkit import PromptSession, print_formatted_text, prompt
# from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from center import (alxp, cliout, i18n, invert_dict_B, isZeilenAngabe,
                    isZeilenAngabe_betweenKommas, moduloA, primfaktoren,
                    primRepeat, retaPromptHilfe, teiler, textHatZiffer, x)
from LibRetaPrompt import (BereichToNumbers2, PromptModus,
                           gebrochenErlaubteZahlen, isReTaParameter,
                           notParameterValues, stextFromKleinKleinKleinBefehl,
                           verifyBruchNganzZahlBetweenCommas, verkuerze_dict,
                           wahl15)
# import reta
from nestedAlx import (ComplSitua, NestedCompleter, ausgabeParas, befehle,
                       befehle2, hauptForNeben, kombiMainParas, mainParas,
                       reta, retaProgram, spalten, spaltenDict, zeilenParas)
from word_completerAlx import WordCompleter

i18nRP = i18n.retaPrompt
wahl15["_"] = wahl15["_15"]
befehleBeenden = i18nRP.befehleBeenden
# befehleBeenden = {"ende", "exit", "quit", "q", ":q"}
infoLog = False


def anotherOberesMaximum(c, maxNum):
    maximizing = list(BereichToNumbers2(c, False, 0))
    if len(maximizing) > 0:
        maximizing.sort()
        maxNum2 = maximizing[-1]
    else:
        maxNum2 = maxNum
    return (
        "--" + i18n.zeilenParas["oberesmaximum"] + "=" + str(max(maxNum, maxNum2) + 1)
    )


class CharType(Enum):
    decimal = 0
    alpha = 1
    neithernor = 2
    begin = 3


def newSession(history=False):
    if history:
        return PromptSession(
            history=FileHistory(os.path.expanduser("~") + os.sep + ".ReTaPromptHistory")
        )
    else:
        return PromptSession()


def returnOnlyParasAsList(textList: str):
    liste = []
    for t in textList:
        if isReTaParameter(t):
            liste += [t]
    return liste


# def externCommand(cmd: str, StrNummern: str):
#    nummern: list[int] = list(BereichToNumbers2(StrNummern, False, 0))
#    nummern.sort()
#    nummernStr: list[str] = [str(nummer) for nummer in nummern]
#    try:
#        process = subprocess.Popen(
#            [os.path.dirname(__file__) + os.sep + cmd, *nummernStr]
#        )
#        process.wait()
#    except:
#        pass
#


def grKl(A: set, B: set) -> tuple:
    """
    Gibt 2 Mengen zurück: eine Menge aus allem, das größer ist als im ersten Parameter aus dem zweiten Parameter
    und in die zweite Menge kommt alles, das kleiner ist, als in der ersten Menge aus der zweiten Menge
    """
    C = set()
    D = set()
    if len(B) == 0:
        return A, A
    for a in A:
        if a > max(B):
            C.add(a)
        elif a < min(B):
            D.add(a)
    return C, D


def getDictLimtedByKeyList(d: dict, keys) -> dict:
    """
    Gibt ein dict zurück, das aus einem dict gebildet wird, aber davon nur das nimmt, was an mehreren keys genommen werden soll.
    """
    return OrderedDict({k: d[k] for k in keys if k in d})


def bruchSpalt(text) -> list:
    """
    Gibt eine Liste aus Tupeln zurück, die entweder einen bis mehrere oder zwei Werte enthalten.
    Eingabe sind Brüche gemischt mit Textwerten
    Das Ergebnis bei zwei Werten ist der Bruch
    Bei ein bis mehreren Werten, also auch 2 handelt es sich um die Textwerte, welche zwischen den Brüchen waren.
    Die Reihenfolge vom Ergebnis ist die Gleiche, wie bei dem Eingabe-Text
    """
    if type(text) is not str:
        return []
    bruchSpalten: list[str] = text.split("/")
    bruchSpaltenNeu = []
    bruchSpaltenNeu2 = []
    if len(bruchSpalten) < 2:
        """Ein Bruch hat immer mindestens 2 Zahlen"""
        return []
    keineZahl = OrderedDict()
    for k, bS in enumerate(bruchSpalten):
        keineZahlBefore = keineZahl
        zahl, keineZahl, bsNeu = OrderedDict(), OrderedDict(), []
        countChar = 0
        countNumber = 0
        wasNumber = False
        goNext = 0
        for char in bS:
            if char.isdecimal():
                """alles was Zahlen sind"""
                if not wasNumber:
                    goNext += 1
                try:
                    zahl[goNext] += char
                except KeyError:
                    zahl[goNext] = char
                wasNumber = True
                countNumber += 1
                countChar = 0
            else:
                """alles was keine Zahlen sind"""
                if wasNumber:
                    goNext += 1
                try:
                    keineZahl[goNext] += char
                except KeyError:
                    keineZahl[goNext] = char
                wasNumber = False
                countChar += 1
                countNumber = 0
        flag: bool = False
        allVergleich: list[bool] = [
            zahl > c for c, zahl in zip(keineZahl.keys(), zahl.keys())
        ]
        """bool Liste wann es keine ist und wann eine zahl im string"""
        zahlSet: set = set(zahl.keys())
        keineZahlSet: set = set(keineZahl.keys())
        if len(zahlSet) == 0:
            return []
        anfang, ende = k == 0, k == len(bruchSpalten) - 1
        if anfang and all(allVergleich):
            flag = True
        elif ende and not any(allVergleich):
            flag = True
        elif (
            not anfang
            and not ende
            and keineZahlSet.issubset(range(min(zahlSet) + 1, max(zahlSet)))
        ):
            flag = True
        else:
            flag = False
        if flag is False:
            return []
        # bsAlt = bsNeu
        if len(keineZahlSet) > 0:
            zahlenGroesserSet, zahlenKleinerSet = grKl(zahlSet, keineZahlSet)
            """siehe erklärung der Fkt in Fkt"""
            zahlenKleinerDict: dict = getDictLimtedByKeyList(zahl, zahlenKleinerSet)
            zahlenGroesserDict: dict = getDictLimtedByKeyList(zahl, zahlenGroesserSet)
            """siehe erklärung der Fkt in Fkt"""
            if k == len(bruchSpalten) - 1 and len(zahlenGroesserDict) > 0:
                return []
            bsNeu = [zahlenKleinerDict, keineZahl, zahlenGroesserDict]
        elif k == 0 or k == len(bruchSpalten) - 1:
            bsNeu = [zahl]
        else:
            return []
        bruchSpaltenNeu += [bsNeu]
        if k == 1:
            vorZahl1 = (
                () if len(bruchSpaltenNeu[0]) == 1 else bruchSpaltenNeu[0][1].values()
            )
            vorZahl1 = tuple(vorZahl1)
            zahl1 = (
                bruchSpaltenNeu[0][0].values()
                if len(bruchSpaltenNeu[0]) == 1
                else bruchSpaltenNeu[0][2].values()
            )
            zahl2 = bruchSpaltenNeu[1][0].values()
            zahl1 = tuple(zahl1)
            zahl2 = tuple(zahl2)
            if k == len(bruchSpalten) - 1:
                nachZahl2 = (
                    ()
                    if len(bruchSpaltenNeu[-1]) == 1
                    else bruchSpaltenNeu[-1][1].values()
                )
                nachZahl2 = tuple(nachZahl2)
                bruchSpaltenNeu2 += [vorZahl1, zahl1 + zahl2, nachZahl2]
            else:
                bruchSpaltenNeu2 += [vorZahl1, zahl1 + zahl2]
        elif k == len(bruchSpalten) - 1 and k > 1:
            vorZahl1 = (
                () if len(bruchSpaltenNeu[-2]) == 1 else bruchSpaltenNeu[-2][1].values()
            )
            vorZahl1 = tuple(vorZahl1)
            zahl1 = (
                bruchSpaltenNeu[-2][0].values()
                if len(bruchSpaltenNeu[-2]) == 1
                else bruchSpaltenNeu[-2][2].values()
            )
            zahl2 = bruchSpaltenNeu[-1][0].values()
            zahl1 = tuple(zahl1)
            zahl2 = tuple(zahl2)
            nachZahl2 = (
                () if len(bruchSpaltenNeu[-1]) == 1 else bruchSpaltenNeu[-1][1].values()
            )
            nachZahl2 = tuple(nachZahl2)
            bruchSpaltenNeu2 += [vorZahl1, zahl1 + zahl2, nachZahl2]
        elif k > 1:
            vorZahl1 = (
                () if len(bruchSpaltenNeu[-2]) == 1 else bruchSpaltenNeu[-2][1].values()
            )
            vorZahl1 = tuple(vorZahl1)
            zahl1 = (
                bruchSpaltenNeu[-2][0].values()
                if len(bruchSpaltenNeu[-2]) == 1
                else bruchSpaltenNeu[-2][2].values()
            )
            zahl2 = bruchSpaltenNeu[-1][0].values()
            zahl1 = tuple(zahl1)
            zahl2 = tuple(zahl2)
            bruchSpaltenNeu2 += [vorZahl1, zahl1 + zahl2]
            # return bruchSpaltenNeu, bruchSpaltenNeu2
    return bruchSpaltenNeu2


def dictToList(dict_: dict) -> list:
    liste = []
    for key, value in dict_.items():
        liste += [value]
    return liste


def createRangesForBruchLists(bruchList: list) -> tuple:
    n1, n2 = [], []
    listenRange: range = range(0)
    listenRangeUrsprung: range = range(0)
    flag = 0
    # ergebnis: list[tuple[range | str]] = []
    ergebnis = []
    if (
        len(bruchList) == 3
        and len(bruchList[0]) == 0
        and len(bruchList[1]) == 2
        and len(bruchList[2]) == 0
        and (bruchList[1][0] + bruchList[1][1]).isdecimal()
    ):
        return [int(bruchList[1][0])], bruchList[1][1]
    for i, b in enumerate(bruchList):
        if flag == -1:
            return []
        if flag > 3:
            """illegal"""
            return []
        elif flag == 3:
            """Es war ein Bruch"""
            ergebnis += [str(n2[-2]), "-", str(n2[-1])]

            listenRange = range(int(n1[-2]), int(n1[-1]) + 1)
            listenRangeUrsprung = listenRange
            flag = -1
        if len(b) == 2 and (b[0] + b[1]).isdecimal():
            """Es ist ein Bruch"""
            if (
                len(bruchList) >= i
                and len(bruchList[i + 1]) == 1
                and bruchList[i + 1][0] == "-"
                and flag == 0
            ) or (
                i > 0
                and len(bruchList[i - 1]) == 1
                and bruchList[i - 1][0] == "-"
                and flag == 2
            ):
                n1 += [int(b[0])]
                n2 += [int(b[1])]
                flag += 1
            else:
                ergebnis += [b[1]]
                if (
                    len(listenRange) > 0
                    and i > 0
                    and len(bruchList[i - 1]) == 1
                    and bruchList[i - 1][0] == "+"
                ):
                    listenRange2 = []
                    for lr in listenRangeUrsprung:
                        listenRange2 += [lr + int(b[0]), lr - int(b[0])]
                    listenRange = listenRange2
                elif len(listenRange) == 0:
                    listenRange = [int(b[0])]
                    listenRangeUrsprung = listenRange
        elif len(b) == 1 and b[0] == "-" and flag > 0:
            flag += 1

        else:
            """Es ist kein Bruch"""
            flag = 0
            ergebnis += [*b]
    ergebnis2 = "".join(ergebnis)
    return listenRange, ergebnis2


def speichern(ketten, platzhalter, text):
    global promptMode2, textDazu0
    bedingung1 = len(platzhalter) > 0
    bedingung2 = len(ketten) > 0
    if bedingung1 or bedingung2:
        if bedingung1:
            ifJoinReTaBefehle = True
            rpBefehlE = " "
            for rpBefehl in (text, platzhalter):
                rpBefehlSplitted = str(rpBefehl).split()
                if len(rpBefehlSplitted) > 0 and rpBefehlSplitted[0] == "reta":
                    rpBefehlE += " ".join(rpBefehlSplitted[1:]) + " "
                else:
                    ifJoinReTaBefehle = False
            if ifJoinReTaBefehle:
                platzhalter = "reta " + rpBefehlE
            else:
                # nochmal für nicht Kurzbefehle befehle, also ohne "reta" am Anfang
                textUndPlatzHalterNeu = []
                langKurzBefehle = []
                for rpBefehl in text.split() + platzhalter.split():
                    if rpBefehl in befehle and len(rpBefehl) > 1:
                        langKurzBefehle += [rpBefehl]
                    else:
                        textUndPlatzHalterNeu += [rpBefehl]
                ifJoinReTaBefehle = True
                rpBefehlE = " "
                for rpBefehl in textUndPlatzHalterNeu:
                    rpBefehlSplitted = str(rpBefehl).split()
                    if len(rpBefehlSplitted) > 0 and rpBefehlSplitted[0] != "reta":
                        rpBefehlE += " ".join(rpBefehlSplitted) + " "
                    else:
                        ifJoinReTaBefehle = False
                if ifJoinReTaBefehle:
                    rpBefehle2 = " "
                    charTuep = CharType.begin
                    stilbruch = False
                    zeichenKette = []
                    zahlenBereich = " "
                    alt_i = -1
                    for i, rpBefehl in enumerate(textUndPlatzHalterNeu):
                        for zeichen in rpBefehl:
                            charTuepDavor = charTuep
                            if zeichen.isalpha():
                                charTuep = CharType.alpha
                            elif zeichen.isdecimal():
                                charTuep = CharType.decimal
                            else:
                                charTuep = CharType.neithernor
                            if (
                                charTuep != charTuepDavor
                                and charTuepDavor != CharType.begin
                            ):
                                stilbruch = True
                            if not zeichen.isspace():
                                if zeichen in [",", "-"] or zeichen.isdecimal():
                                    if i == alt_i:
                                        zahlenBereich += " " + zeichen + " "
                                    else:
                                        zahlenBereich += zeichen
                                else:
                                    zeichenKette += [zeichen]
                        alt_i = i
                    if stilbruch:
                        rpBefehle2 = " ".join(zeichenKette) + zahlenBereich
                    platzhalter = rpBefehle2 + " " + (" ".join(langKurzBefehle))

        # vielleicht programmier ich hier noch weiter
        if bedingung2 and False:
            ifJoinReTaBefehle = True
            rpBefehlE = ""
            for rpBefehl in ketten:
                rpBefehlSplitted = rpBefehl
                if len(rpBefehl) > 0 and rpBefehl[0] == "reta":
                    rpBefehlE += " ".join(rpBefehl[1:]) + " "
                else:
                    ifJoinReTaBefehle = False
            if ifJoinReTaBefehle:
                platzhalter = "reta " + rpBefehlE

    else:
        platzhalter = "" if text is None else str(text)
    text = ""
    if platzhalter != "":
        promptMode2 = PromptModus.AusgabeSelektiv
    else:
        promptMode2 = PromptModus.normal
    (
        bedingungX,
        bruecheX,
        cX,
        ketten2X,
        maxNum2X,
        stextX,
        zahlenAngaben_X,
        ifKurzKurz_X,
    ) = promptVorbereitungGrosseAusgabe(
        ketten,
        platzhalter,
        PromptModus.normal,
        PromptModus.normal,
        PromptModus.normal,
        platzhalter,
        [],
    )

    # textDazu0 = platzhalter.split()
    textDazu0 = stextX
    return ketten, platzhalter, text


def PromptScope():
    global promptMode2, textDazu0
    (
        befehleBeenden,
        ketten,
        loggingSwitch,
        nochAusageben,
        platzhalter,
        promptDavorDict,
        promptMode,
        startpunkt1,
        text,
        nurEinBefehl,
        immerEbefehlJa,
    ) = PromptAllesVorGroesserSchleife()
    while len(set(text.split()) & set(befehleBeenden)) == 0:
        warBefehl = False
        promptModeLast = promptMode

        if promptMode not in (
            PromptModus.speicherungAusgaben,
            PromptModus.speicherungAusgabenMitZusatz,
        ):
            befehlDavor, text, textE = promptInput(
                loggingSwitch,
                platzhalter,
                promptDavorDict,
                promptMode,
                startpunkt1,
                text,
                nurEinBefehl,
                immerEbefehlJa,
            )
            ketten, platzhalter, text = promptSpeicherungA(
                ketten, platzhalter, promptMode, text
            )

        else:
            text = promptSpeicherungB(nochAusageben, platzhalter, promptMode, text)
            textE = []

        if promptMode == PromptModus.loeschenSelect:
            platzhalter, promptMode, text = PromptLoescheVorSpeicherungBefehle(
                platzhalter, promptMode, text
            )
            continue

        promptMode = PromptModus.normal

        if text is not None:
            stext: list = text.split()
        else:
            stext: list = []

        stextE = stext + textE
        if (
            (i18n.befehle2["S"] in stext)
            or (i18n.befehle2["BefehlSpeichernDanach"] in stext)
        ) and len(stext) == 1:
            promptMode = PromptModus.speichern
            continue
        elif (
            (i18n.befehle2["s"] in stext)
            or (i18n.befehle2["BefehlSpeichernDavor"] in stext)
        ) and len(stext) == 1:
            ketten, platzhalter, text = speichern(ketten, platzhalter, befehlDavor)
            promptMode = PromptModus.normal
            continue
        elif len(
            set(stext)
            - {
                i18n.befehle2["s"],
                i18n.befehle2["BefehlSpeichernDavor"],
                i18n.befehle2["S"],
                i18n.befehle2["BefehlSpeichernDanach"],
            }
        ) > 0 and (
            len(
                set(stext)
                & {
                    i18n.befehle2["s"],
                    i18n.befehle2["BefehlSpeichernDavor"],
                    i18n.befehle2["S"],
                    i18n.befehle2["BefehlSpeichernDanach"],
                }
            )
            == 1
        ):
            stextB = copy(stext)
            for val in (
                i18n.befehle2["s"],
                i18n.befehle2["S"],
                i18n.befehle2["BefehlSpeichernDavor"],
                i18n.befehle2["BefehlSpeichernDanach"],
            ):
                try:
                    stextB.remove(val)
                except ValueError:
                    pass
            ketten, platzhalter, text = speichern(ketten, platzhalter, " ".join(stextB))
            stext = []
            stextE = []
            text = ""
            befehlDavor = ""
            promptMode = PromptModus.normal
            continue
        elif (
            (i18n.befehle2["o"] in stext) or ("BefehlSpeicherungAusgeben" in stext)
        ) and len(stext) == 1:
            promptMode = PromptModus.speicherungAusgaben
            continue
        elif (
            (i18n.befehle2["o"] in stext) or ("BefehlSpeicherungAusgeben" in stext)
        ) and len(set(stext) - {i18n.befehle2["o"], "BefehlSpeicherungAusgeben"}) > 1:
            nochAusageben = stext
            promptMode = PromptModus.speicherungAusgabenMitZusatz
            continue
        elif (
            (i18n.befehle2["l"] in stext) or ("BefehlSpeicherungLöschen" in stext)
        ) and len(stext) == 1:
            print(str([{i + 1, a} for i, a in enumerate(platzhalter.split())]))
            print(i18nRP.promptModeSatz.format(promptMode, promptMode2))
            promptMode = PromptModus.loeschenSelect
            continue

        (
            IsPureOnlyReTaCmd,
            brueche,
            c,
            ketten,
            maxNum,
            stext,
            zahlenAngaben_,
            ifKurzKurz,
        ) = promptVorbereitungGrosseAusgabe(
            ketten,
            platzhalter,
            promptMode,
            promptMode2,
            promptModeLast,
            text,
            textDazu0,
        )
        stextE = stext + textE
        loggingSwitch = PromptGrosseAusgabe(
            IsPureOnlyReTaCmd,
            befehleBeenden,
            brueche,
            c,
            ketten,
            loggingSwitch,
            maxNum,
            stext,
            text,
            warBefehl,
            zahlenAngaben_,
            ifKurzKurz,
            nurEinBefehl,
            stextE,
        )


def PromptGrosseAusgabe(
    IsPureOnlyReTaCmd,
    befehleBeenden,
    brueche,
    c,
    ketten,
    loggingSwitch,
    maxNum,
    stext,
    text,
    warBefehl,
    zahlenAngaben_,
    ifKurzKurz,
    nurEinBefehl,
    stextE,
):
    (
        EsGabzahlenAngaben,
        zahlenReiheKeineWteiler,
        bruch_GanzZahlReziproke,
        fullBlockIsZahlenbereichAndBruch,
        rangesBruecheDict,
        rangesBruecheDictReverse,
    ) = (False, "", [], False, {}, {})
    if not IsPureOnlyReTaCmd:
        (
            bruch_GanzZahlReziproke,
            c,
            zahlenReiheKeineWteiler,
            fullBlockIsZahlenbereichAndBruch,
            rangesBruecheDict,
            EsGabzahlenAngaben,
            rangesBruecheDictReverse,
            stext,
        ) = bruchBereichsManagementAndWbefehl(c, stext, zahlenAngaben_)
    if i18n.befehle2["mulpri"] in stextE or i18n.befehle2["p"] in stextE:
        stext += [i18n.befehle2["multis"], i18n.befehle2["prim"]]
        stextE += [i18n.befehle2["multis"], i18n.befehle2["prim"]]

    if (
        "".join(("--", i18n.ausgabeParas["art"], "=", i18n.ausgabeArt["bbcode"]))
        in stextE
        and "reta" == stextE[0]
    ):
        if "--" + i18n.ausgabeParas["nocolor"] in stextE:
            print("[code]" + text + "[/code]")
        else:
            cliout("[code]" + text + "[/code]", True, "bbcode")
    if (
        ifKurzKurz
        and i18n.befehle2["keineEinZeichenZeilenPlusKeineAusgabeWelcherBefehlEsWar"]
        not in stextE
    ):
        print(i18nRP.promptModeSatz2.format(" ".join(stextE), text))
    if (i18n.befehle2["abc"] in stextE or i18n.befehle2["abcd"] in stextE) and len(
        stext
    ) == 2:
        warBefehl = True
        buchstabe: str
        if stext[0] == i18n.befehle2["abc"] or stext[0] == i18n.befehle2["abcd"]:
            buchstaben = stext[1]
        else:
            buchstaben = stext[0]
        print(
            str(
                " ".join(
                    [
                        "".join(str(ord(buchstabe.lower()) - 96))
                        for buchstabe in buchstaben
                    ]
                )
            )
        )
    if len({i18n.befehle2["befehle"]} & set(stextE)) > 0:
        warBefehl = True
        print("Befehle: " + str(befehle)[1:-1])
    if len({"help", "hilfe"} & set(stextE)) > 0 or (
        "h" in stextE
        and i18n.befehle2["abc"] not in stextE
        and i18n.befehle2["abcd"] not in stextE
    ):
        warBefehl = True
        retaPromptHilfe()
    bedingungZahl, bedingungBrueche = (
        EsGabzahlenAngaben,
        (len(bruch_GanzZahlReziproke) > 0 or len(rangesBruecheDict) > 0)
        or len(rangesBruecheDictReverse) > 0,
    )
    if IsPureOnlyReTaCmd:
        warBefehl = True
        import reta

        reta.Program(stextE)

    if len(bruch_GanzZahlReziproke) > 0 and textHatZiffer(bruch_GanzZahlReziproke):
        zeiln3 = "--vorhervonausschnitt=" + bruch_GanzZahlReziproke
        zeiln4 = ""
    else:
        zeiln3 = "--vorhervonausschnitt=0"
        zeiln4 = ""
    if bedingungZahl:
        zahlenBereiche = str(c).strip()
        # x("890ßfvsdwer", [zahlenBereiche, textHatZiffer(zahlenBereiche)])
        if textHatZiffer(zahlenBereiche):
            if i18n.befehle2["einzeln"] not in stextE and (
                (i18n.befehle2["vielfache"] in stextE)
                or (
                    i18n.befehle2["v"] in stextE
                    and i18n.befehle2["abc"] not in stextE
                    and i18n.befehle2["abcd"] not in stextE
                )
            ):
                if len(set(stext) & {i18n.befehle2["teiler"], i18n.befehle2["w"]}) == 0:
                    zeiln1 = "--vielfachevonzahlen=" + zahlenReiheKeineWteiler
                else:
                    zeiln1 = ""
                zeiln2 = "".join(
                    [
                        "--vorhervonausschnitt=",
                        zahlenBereiche,
                        ",",
                        ",".join(
                            [
                                i18n.befehle2["v"] + str(z)
                                for z in zahlenReiheKeineWteiler.split(",")
                            ]
                        ),
                    ]
                )

                # zeiln2 = ""
            else:
                zeiln1 = "--vorhervonausschnitt=" + zahlenBereiche

                zeiln2 = anotherOberesMaximum(c, maxNum)
        else:
            zeiln1 = "--vorhervonausschnitt=0"
            zeiln2 = ""

    else:
        zeiln1 = ""
        zeiln2 = ""

    if bedingungZahl:
        if (len({i18n.befehle2["thomas"]} & set(stextE)) > 0) or (
            "t" in stextE
            and i18n.befehle2["abc"] not in stextE
            and i18n.befehle2["abcd"] not in stextE
        ):
            warBefehl = True
            import reta

            kette = [
                "reta",
                "-zeilen",
                zeiln1,
                zeiln2,
                "-spalten",
                "--galaxie=thomas",
                "--breite=0",
                "-ausgabe",
                "--spaltenreihenfolgeundnurdiese=2",
                *[
                    "--keineleereninhalte"
                    if i18n.befehle2[
                        "keineEinZeichenZeilenPlusKeineAusgabeWelcherBefehlEsWar"
                    ]
                    in stextE
                    else ""
                ],
            ] + returnOnlyParasAsList(stextE)
            kette += ketten
            if (
                i18n.befehle2["keineEinZeichenZeilenPlusKeineAusgabeWelcherBefehlEsWar"]
                not in stextE
            ):
                print(" ".join(kette))
            reta.Program(
                kette,
            )

    if fullBlockIsZahlenbereichAndBruch and (bedingungZahl or bedingungBrueche):
        if len(
            {
                i18n.befehle2["absicht"],
                i18n.befehle2["absichten"],
                i18n.befehle2["motiv"],
                i18n.befehle2["motive"],
            }
            & set(stextE)
        ) > 0 or (
            ((i18n.befehle2["a"] in stextE) != (i18n.befehle2["mo"] in stextE))
            and i18n.befehle2["abc"] not in stextE
            and i18n.befehle2["abcd"] not in stextE
        ):
            warBefehl = True

            if len(c) > 0:
                retaExecuteNprint(
                    ketten, stextE, zeiln1, zeiln2, ["--menschliches=motivation"], "1"
                )
            # x("9vnw3dfg345", bruch_GanzZahlReziproke)
            if (
                len(bruch_GanzZahlReziproke) > 0
                and textHatZiffer(bruch_GanzZahlReziproke)
                and zeiln3 != ""
            ):
                retaExecuteNprint(
                    ketten, stextE, zeiln3, zeiln4, ["--menschliches=motivation"], "3"
                )

            if len(rangesBruecheDict) > 0:
                for nenner, zaehler in rangesBruecheDict.items():
                    retaExecuteNprint(
                        ketten,
                        stextE,
                        "--vorhervonausschnitt=" + ",".join(zaehler),
                        "",
                        ["--gebrochengalaxie=" + str(nenner)],
                        "2",
                    )
            elif len(rangesBruecheDictReverse) > 0:
                for nenner, zaehler in rangesBruecheDictReverse.items():
                    # x("346dfg", rangesBruecheDictReverse)
                    retaExecuteNprint(
                        ketten,
                        stextE,
                        "--vorhervonausschnitt=" + ",".join(zaehler),
                        "",
                        ["--gebrochengalaxie=" + str(nenner)],
                        "1",
                    )

        eigN, eigR = [], []
        for aa in stextE:
            if i18n.EIGS_N_R[0] == aa[:4]:
                eigN += [aa[4:]]
            if i18n.EIGS_N_R[1] == aa[:4]:
                eigR += [aa[4:]]

        if len(eigN) > 0:
            warBefehl = True
            if len(c) > 0:
                retaExecuteNprint(
                    ketten,
                    stextE,
                    zeiln1,
                    ["--konzept=" + ",".join(eigN)],
                    None,
                )

        if len(eigR) > 0:
            warBefehl = True
            if len(c) > 0:
                retaExecuteNprint(
                    ketten,
                    stextE,
                    zeiln1,
                    zeiln2,
                    ["--konzept=" + ",".join(eigR)],
                    None,
                )

        if len({"universum"} & set(stextE)) > 0 or (
            "u" in stextE
            and i18n.befehle2["abc"] not in stextE
            and i18n.befehle2["abcd"] not in stextE
        ):
            warBefehl = True
            if len(c) > 0:
                retaExecuteNprint(
                    ketten,
                    stextE,
                    zeiln1,
                    zeiln2,
                    ["--universum=transzendentalien,komplexitaet,ontologie"],
                    "1,3,4",
                )

            if (
                len(bruch_GanzZahlReziproke) > 0
                and textHatZiffer(bruch_GanzZahlReziproke)
                and zeiln3 != ""
            ):
                retaExecuteNprint(
                    ketten,
                    stextE,
                    zeiln3,
                    zeiln4,
                    ["--universum=transzendentaliereziproke"],
                    "1",
                )

            nennerZaehlerGleich = []
            if len(rangesBruecheDict) > 0:
                for nenner, zaehler in rangesBruecheDict.items():
                    hierBereich = ",".join(zaehler)
                    retaExecuteNprint(
                        ketten,
                        stextE,
                        "--vorhervonausschnitt=" + hierBereich,
                        "",
                        ["--gebrochenuniversum=" + str(nenner)],
                        "2",
                    )

            elif len(rangesBruecheDictReverse) > 0:
                for nenner, zaehler in rangesBruecheDictReverse.items():
                    hierBereich = ",".join(zaehler)
                    print("S")
                    retaExecuteNprint(
                        ketten,
                        stextE,
                        "--vorhervonausschnitt=" + hierBereich,
                        "",
                        ["--gebrochenuniversum=" + str(nenner)],
                        "1",
                    )
                    nennerZaehlerGleich += findEqualNennerZaehler(
                        hierBereich, nenner, nennerZaehlerGleich
                    )
            if len(nennerZaehlerGleich) != 0:
                nennerZaehlerGleich = ",".join(nennerZaehlerGleich)
                retaExecuteNprint(
                    ketten,
                    stextE,
                    "--vorhervonausschnitt=" + nennerZaehlerGleich,
                    "",
                    ["--universum=verhaeltnisgleicherzahl"],
                    "1",
                )
    if bedingungZahl:
        if len({"prim24", "primfaktorzerlegungModulo24"} & set(stextE)) > 0:
            warBefehl = True
            for arg in zahlenReiheKeineWteiler.split(","):
                if arg.isdecimal():
                    print(
                        str(arg)
                        + ": "
                        + str(primRepeat(primfaktoren(int(arg), True)))[1:-1]
                        .replace("'", "")
                        .replace(", ", " ")
                    )

        if len({"prim", "primfaktorzerlegung"} & set(stextE)) > 0:
            warBefehl = True
            for arg in zahlenReiheKeineWteiler.split(","):
                if arg.isdecimal():
                    print(
                        str(arg)
                        + ": "
                        + str(primRepeat(primfaktoren(int(arg))))[1:-1]
                        .replace("'", "")
                        .replace(", ", " ")
                    )

        if len({"multis"} & set(stextE)) > 0 or (
            "mu" in stextE
            and i18n.befehle2["abc"] not in stextE
            and i18n.befehle2["abcd"] not in stextE
        ):
            warBefehl = True
            import reta

            listeStrWerte = zahlenReiheKeineWteiler.split(",")
            try:
                mult(listeStrWerte)
            except NameError:
                from multis import mult

                mult(listeStrWerte)

            # externCommand("prim", c)

        if len({"mond"} & set(stextE)) > 0:
            warBefehl = True
            retaExecuteNprint(
                ketten,
                stextE,
                zeiln1,
                zeiln2,
                ["--bedeutung=gestirn"],
                "3-6",
            )

        if len({"procontra"} & set(stextE)) > 0:
            warBefehl = True
            retaExecuteNprint(
                ketten,
                stextE,
                zeiln1,
                zeiln2,
                [
                    "--procontra=pro,contra,gegenteil,harmonie,helfen,hilfeerhalten,gegenposition,pronutzen,nervig,nichtauskommen,nichtdagegen,keingegenteil,nichtdafuer,hilfenichtgebrauchen,nichthelfenkoennen,nichtabgeneigt,unmotivierbar,gegenspieler,sinn,vorteile,veraendern,kontrollieren,einheit"
                ],
                None,
            )
        if len({"modulo"} & set(stextE)) > 0:
            warBefehl = True
            moduloA([str(num) for num in BereichToNumbers2(c)])
        if len({"alles"} & set(stextE)) > 0:
            warBefehl = True
            retaExecuteNprint(
                ketten,
                stextE,
                zeiln1,
                zeiln2,
                ["--alles"],
                None,
            )

        if len({"primzahlkreuz"} & set(stextE)) > 0:
            warBefehl = True
            retaExecuteNprint(
                ketten,
                stextE,
                zeiln1,
                anotherOberesMaximum(c, 1028),
                ["--bedeutung=primzahlkreuz"],
                None,
            )
            import reta

        if (len({i18n.befehle2["richtung"]} & set(stextE)) > 0) or (
            "r" in stextE
            and i18n.befehle2["abc"] not in stextE
            and i18n.befehle2["abcd"] not in stextE
        ):
            warBefehl = True
            retaExecuteNprint(
                ketten,
                stextE,
                zeiln1,
                zeiln2,
                ["--primzahlwirkung=Galaxieabsicht"],
                None,
            )

        if (
            len(stextE) > 0
            and any([token[:3] == "15_" for token in stextE])
            and i18n.befehle2["abc"] not in stextE
            and i18n.befehle2["abcd"] not in stextE
        ):
            warBefehl = True
            import reta

            try:
                befehle15 = []
                for token in stextE:
                    if token[:3] == "15_":
                        befehle15 += [wahl15[token[2:]]]
                grundstruk = ",".join(befehle15)
                retaExecuteNprint(
                    ketten,
                    stextE,
                    zeiln1,
                    zeiln2,
                    ["--grundstrukturen=" + grundstruk],
                    None,
                )
            except:
                pass
    if (
        len(stext) == 3
        and i18n.befehle2["abstand"] in stext
        and any([s.isdecimal() for s in stext])
    ):
        flag = False
        for i, s in enumerate(stext):
            if s.isdecimal():
                zahlNum = i
            s = s.split("-")
            if len(s) == 2 and s[0].isdecimal() and s[1].isdecimal():
                flag = True
                bereich = (int(s[0]), int(s[1]))
        if flag:
            warBefehl = True
            zahl = int(stext[zahlNum])
            zeige = {b: abs(b - zahl) for b in range(bereich[0], bereich[1] + 1)}
            print(str(zeige)[1:-1])
    elif i18n.befehle2["abstand"] in stext:
        print(
            "der Befehl 'abstand' ist nur erlaubt mit 2 weiteren Angaben mit Leerzeichen getrennt, einer Zahl und einem Zahlenbereich, z.B. 'abstand 7 17-25'"
        )

    loggingSwitch, warBefehl = PromptVonGrosserAusgabeSonderBefehlAusgaben(
        loggingSwitch, stext, text, warBefehl
    )
    if len(nurEinBefehl) > 0:
        stext = copy(befehleBeenden)
        stextE = copy(befehleBeenden)
        nurEinBefehl = " ".join(befehleBeenden)
        exit()
    if not warBefehl and len(stext) > 0 and stextE[0] not in befehleBeenden:
        if len(set(stext) & set(befehle)) > 0:
            print(
                "Dies ('"
                + " ".join(stextE)
                + "') ist tatsächlich ein Befehl (oder es sind mehrere), aber es gibt nichts auszugeben.",
            )
        else:
            print("Das ist kein Befehl! -> '{}''".format(" ".join(stextE)))
    return loggingSwitch


def retaExecuteNprint(
    ketten: list,
    stextE: list,
    zeiln1: str,
    zeiln2: str,
    welcheSpalten: list[str],
    ErlaubteSpalten: str,
):
    import reta

    kette = [
        "reta",
        "-zeilen",
        zeiln1,
        zeiln2,
        "-spalten",
        *welcheSpalten,
        "--breite=0",
        "-ausgabe",
        ("--spaltenreihenfolgeundnurdiese=" + ErlaubteSpalten)
        if ErlaubteSpalten is not None
        else "",
        *[
            "--keineleereninhalte"
            if i18n.befehle2["keineEinZeichenZeilenPlusKeineAusgabeWelcherBefehlEsWar"]
            in stextE
            else ""
        ],
    ] + returnOnlyParasAsList(stextE)
    kette += ketten
    if (
        i18n.befehle2["keineEinZeichenZeilenPlusKeineAusgabeWelcherBefehlEsWar"]
        not in stextE
    ):
        print(" ".join(kette))
    reta.Program(
        kette,
    )


def findEqualNennerZaehler(hierBereich, nenner, nennerZaehlerGleich):
    hierBereich2 = BereichToNumbers2(str(hierBereich))
    nenner2 = BereichToNumbers2(str(nenner))
    for nn3 in nenner2:
        for hB3 in hierBereich2:
            if nn3 == hB3 and nn3 not in [0, 1]:
                nennerZaehlerGleich += [str(nn3)]
    return nennerZaehlerGleich


def bruchBereichsManagementAndWbefehl(c, stext, zahlenAngaben_):
    bruch_GanzZahlReziproke = []
    bruch_GanzZahlReziprokeAbzug = []
    bruch_KeinGanzZahlReziproke = {}
    bruch_KeinGanzZahlReziprokeAbzug = {}
    bruch_KeinGanzZahlReziprok_ = []
    fullBlockIsZahlenbereichAndBruch = True
    rangesBruecheDict = {}
    rangesBruecheDictReverse: dict = {}
    bruch_KeinGanzZahlReziprokeEnDictAbzug = {}
    bruchRanges3Abzug = {}
    valueLenSum = 0
    zahlenAngaben_mehrere = []
    Minusse = {}
    pfaue = {}
    pfaueAbzug = {}
    for g, a in enumerate(stext):
        bruchAndGanzZahlEtwaKorrekterBereich = []
        bruchBereichsAngaben = []
        bruchRanges = []
        abzug = False
        for etwaBruch in a.split(","):
            bruchRange, bruchBereichsAngabe = createRangesForBruchLists(
                bruchSpalt(etwaBruch)
            )
            (
                bruchAndGanzZahlEtwaKorrekterBereich,
                bruchBereichsAngaben,
                bruchRanges,
                zahlenAngaben_,
                etwaAllTrue,
            ) = verifyBruchNganzZahlBetweenCommas(
                bruchAndGanzZahlEtwaKorrekterBereich,
                bruchBereichsAngabe,
                bruchBereichsAngaben,
                bruchRange,
                bruchRanges,
                etwaBruch,
                zahlenAngaben_,
            )
            if etwaAllTrue:
                fullBlockIsZahlenbereichAndBruch = (
                    fullBlockIsZahlenbereichAndBruch
                    and all(bruchAndGanzZahlEtwaKorrekterBereich)
                )

        if fullBlockIsZahlenbereichAndBruch:
            for bruchBereichsAngabe, bruchRange in zip(
                bruchBereichsAngaben, bruchRanges
            ):
                if isZeilenAngabe(bruchBereichsAngabe):
                    bruchRange = {b for b in bruchRange if b > 0}
                    EinsInBereichHier1 = BereichToNumbers2(bruchBereichsAngabe)
                    EinsInBereichHier = 1 in EinsInBereichHier1
                    if (
                        bruchBereichsAngabe[:1] == "-"
                        or bruchBereichsAngabe[:2] == "v-"
                    ):
                        minusHier = True
                        if bruchBereichsAngabe[:2] == "v-":
                            pass
                        if bruchBereichsAngabe[:1] == "-":
                            pass
                    else:
                        minusHier = False
                    if 1 in bruchRange:
                        if minusHier:
                            bruch_GanzZahlReziprokeAbzug += [bruchBereichsAngabe]
                        else:
                            bruch_GanzZahlReziproke += [bruchBereichsAngabe]
                    bruchRangeOhne1 = frozenset(set(bruchRange) - {1})
                    neuerBereich = ",".join(
                        {str(zahl) for zahl in EinsInBereichHier1} - {"1"}
                    )
                    Minusse[tuple(bruchRange)] = minusHier
                    if len(bruchRangeOhne1) > 0:
                        if minusHier:
                            try:
                                bruch_KeinGanzZahlReziprokeAbzug[bruchRangeOhne1] += [
                                    bruchBereichsAngabe
                                ]
                                pfaueAbzug[bruchRangeOhne1] += [
                                    bruchBereichsAngabe[:1] == i18n.befehle2["v"]
                                ]
                            except KeyError:
                                bruch_KeinGanzZahlReziprokeAbzug[bruchRangeOhne1] = [
                                    bruchBereichsAngabe
                                ]
                                pfaueAbzug[bruchRangeOhne1] = [
                                    bruchBereichsAngabe[:1] == i18n.befehle2["v"]
                                ]
                        else:
                            try:
                                bruch_KeinGanzZahlReziproke[bruchRangeOhne1] += [
                                    neuerBereich
                                ]
                                pfaue[bruchRangeOhne1] += [
                                    bruchBereichsAngabe[:1] == i18n.befehle2["v"]
                                ]
                            except KeyError:
                                bruch_KeinGanzZahlReziproke[bruchRangeOhne1] = [
                                    neuerBereich
                                ]
                                pfaue[bruchRangeOhne1] = [
                                    bruchBereichsAngabe[:1] == i18n.befehle2["v"]
                                ]
                    if EinsInBereichHier:
                        neueRange = ",".join([str(zahl) for zahl in bruchRange])
                        stext += [neueRange]
                        EsGabzahlenAngaben = True
                        zahlenAngaben_mehrere += [neueRange]
        zahlenAngaben_mehrere += zahlenAngaben_
    try:
        EsGabzahlenAngaben
    except UnboundLocalError:
        EsGabzahlenAngaben = False
    if (i18n.befehle2["v"] in stext) or (i18n.befehle2["vielfache"] in stext):
        if not (
            (i18n.befehle2["e"] in stext)
            or (
                i18n.befehle2["keineEinZeichenZeilenPlusKeineAusgabeWelcherBefehlEsWar"]
                in stext
            )
        ):
            if (
                len(bruch_GanzZahlReziproke) > 0
                or any(
                    [
                        any([1 in BereichToNumbers2(val2) for val2 in val])
                        for val in bruch_KeinGanzZahlReziproke.values()
                    ]
                )
                or EsGabzahlenAngaben
            ):

                print(
                    'Wenn im Zähler oder Nenner eine 1 ist, so werden davon oft (nicht immer) keine Vielfacher gebildet.\nFür Brüche "n/1=ganze Zahl" gibt es die gewöhnlichen Befehle für ganze Zahlen.\nDas ist eine Design-Entscheidung, die getroffen worden ist.'
                )
        bdNeu = set()
        for bDazu in bruch_GanzZahlReziproke:
            for bDazu in BereichToNumbers2(bDazu):
                i = 1
                rechnung = i * bDazu
                while rechnung < retaProgram.tables.hoechsteZeile[1024]:
                    bdNeu |= {rechnung}
                    i += 1
                    rechnung = i * bDazu
        for bDazu in bruch_GanzZahlReziprokeAbzug:
            if bDazu[:1] == i18n.befehle2["v"]:
                bDazu = bDazu[1:]
            if bDazu[:1] == "-":
                bDazu = bDazu[1:]
            for bDazu in BereichToNumbers2(bDazu):
                i = 1
                rechnung = i * bDazu
                while rechnung < retaProgram.tables.hoechsteZeile[1024]:
                    try:
                        bdNeu -= {rechnung}
                        i += 1
                        rechnung = i * bDazu
                    except:
                        pass
        bruch_GanzZahlReziproke = ",".join((str(b) for b in bdNeu))
        bruchRanges3 = {}
        bruch_KeinGanzZahlReziprokeEnDict = {}
        for k, (brZahlen, no1brueche) in enumerate(bruch_KeinGanzZahlReziproke.items()):

            for no1bruch in no1brueche:
                if len(no1bruch) > 0 and no1bruch[0] == i18n.befehle2["v"]:
                    no1bruch = no1bruch[1:]
                if len(no1bruch) > 0 and no1bruch[0] == "-":
                    no1bruch = no1bruch[1:]
                    abzug = True
                else:
                    abzug = False
                no1brueche = BereichToNumbers2(no1bruch)
                for no1bruch in no1brueche:
                    i = 1
                    rechnung2 = no1bruch * i
                    while rechnung2 in gebrochenErlaubteZahlen:
                        if rechnung2 not in bruch_KeinGanzZahlReziprokeEnDict.values():
                            if abzug:
                                try:
                                    bruch_KeinGanzZahlReziprokeEnDictAbzug[k] += [
                                        rechnung2
                                    ]
                                except KeyError:
                                    bruch_KeinGanzZahlReziprokeEnDictAbzug[k] = [
                                        rechnung2
                                    ]
                            else:
                                try:
                                    bruch_KeinGanzZahlReziprokeEnDict[k] += [rechnung2]
                                except KeyError:
                                    bruch_KeinGanzZahlReziprokeEnDict[k] = [rechnung2]
                        i += 1
                        rechnung2 = no1bruch * i
            for br in brZahlen:
                i = 1
                rechnung = br * i
                while rechnung in gebrochenErlaubteZahlen:
                    if abzug:
                        try:
                            if rechnung not in bruchRanges3Abzug:
                                bruchRanges3Abzug[k] += [rechnung]
                        except KeyError:
                            bruchRanges3Abzug[k] = [rechnung]
                    else:
                        try:
                            if rechnung not in bruchRanges3:
                                bruchRanges3[k] += [rechnung]
                        except KeyError:
                            bruchRanges3[k] = [rechnung]
                    i += 1
                    rechnung = br * i

        for keyRanges, valueRanges in bruchRanges3.items():
            for (
                keyBrueche,
                valueBrueche,
            ) in bruch_KeinGanzZahlReziprokeEnDict.items():
                for eineRange in valueRanges:
                    for einBruch in valueBrueche:
                        if keyRanges == keyBrueche:
                            try:
                                strBruch = str(einBruch)
                                if strBruch not in rangesBruecheDict[eineRange]:
                                    rangesBruecheDict[eineRange] += [strBruch]
                            except KeyError:
                                rangesBruecheDict[eineRange] = [str(einBruch)]
        if len(bruchRanges3Abzug) > 0:
            rangesBruecheDict2 = deepcopy(rangesBruecheDict)
            for AbzugNenners, AbzugZaehlers in zip(
                bruchRanges3Abzug.values(),
                bruch_KeinGanzZahlReziprokeEnDictAbzug.values(),
            ):
                for aNenner, aZaehler in zip(AbzugNenners, AbzugZaehlers):
                    for key, value in zip(
                        bruchRanges3.values(), rangesBruecheDict.values()
                    ):
                        try:
                            if key.index(int(aNenner)) == value.index(str(aZaehler)):
                                try:
                                    value.remove(str(aZaehler))
                                except:
                                    pass
                                try:
                                    key.remove(str(aNenner))
                                except:
                                    pass
                                try:
                                    value.remove(aZaehler)
                                except:
                                    pass
                                try:
                                    key.remove(aNenner)
                                except:
                                    pass
                                rangesBruecheDict2[aNenner] = value
                        except ValueError:
                            pass
            rangesBruecheDict = rangesBruecheDict2
            bruchRanges3Abzug = {}
            bruch_KeinGanzZahlReziprokeEnDictAbzug = {}
    else:
        if (
            len(bruch_GanzZahlReziproke) == 0
            or type(bruch_GanzZahlReziproke) is not str
        ):
            bruch_GanzZahlReziproke = ",".join(
                (
                    ",".join(bruch_GanzZahlReziproke),
                    ",".join(bruch_GanzZahlReziprokeAbzug),
                )
            )
        elif type(bruch_GanzZahlReziproke) is str:
            bruch_GanzZahlReziproke += "," + (
                ",".join(
                    (
                        ",".join(bruch_GanzZahlReziproke),
                        ",".join(bruch_GanzZahlReziprokeAbzug),
                    )
                )
            )

        bruchDict = {}
        for ((bruchRange, bruch_KeinGanzZahlReziprok_), pfauList) in zip(
            bruch_KeinGanzZahlReziproke.items(), pfaue.values()
        ):
            bruch_KeinGanzZahlReziprok_2 = set()
            for pfau, nenners in zip(pfauList, bruch_KeinGanzZahlReziprok_):
                if pfau:
                    nenners = BereichToNumbers2(nenners)
                    for nenner in nenners:
                        i = 1
                        rechnung = i * int(nenner)
                        while rechnung in gebrochenErlaubteZahlen:
                            bruch_KeinGanzZahlReziprok_2 |= {str(rechnung)}
                            i += 1
                            rechnung = i * int(nenner)
                else:
                    bruch_KeinGanzZahlReziprok_2 |= set(nenners.split(","))
            bruch_KeinGanzZahlReziprok_ = ",".join(bruch_KeinGanzZahlReziprok_2)
            for rangePunkt in bruchRange:
                try:
                    bruchDict[rangePunkt] |= {bruch_KeinGanzZahlReziprok_}
                except KeyError:
                    bruchDict[rangePunkt] = {bruch_KeinGanzZahlReziprok_}

                for (
                    bruchRangeA,
                    bruch_KeinGanzZahlReziprok_A,
                ) in bruch_KeinGanzZahlReziprokeAbzug.items():
                    bruch_KeinGanzZahlReziprok_A = ",".join(
                        bruch_KeinGanzZahlReziprok_A
                    )
                    for rangePunktA in bruchRangeA:
                        if rangePunkt == rangePunktA:
                            try:
                                bruchDict[rangePunkt] |= {
                                    bruch_KeinGanzZahlReziprok_,
                                    bruch_KeinGanzZahlReziprok_A,
                                }
                            except KeyError:
                                bruchDict[rangePunkt] = {
                                    bruch_KeinGanzZahlReziprok_,
                                    bruch_KeinGanzZahlReziprok_A,
                                }
        rangesBruecheDict = bruchDict
    rangesBruecheDict2 = {}
    bereicheVorherBestimmtSet = set()
    for key, values in rangesBruecheDict.items():
        bereichVorherBestimmt = [BereichToNumbers2(value) for value in values]
        bereicheVorherBestimmtSet2 = set()
        for b in bereichVorherBestimmt:
            bereicheVorherBestimmtSet2 |= b
        bereicheVorherBestimmtSet |= bereicheVorherBestimmtSet2
        rangesBruecheDict2[key] = list(bereicheVorherBestimmtSet2)
    valueLenSum += len(bereicheVorherBestimmtSet)
    dictLen = len(rangesBruecheDict)
    if dictLen != 0:
        avg = valueLenSum / dictLen
        if avg < 1:
            rangesBruecheDictReverse = invert_dict_B(rangesBruecheDict2)
            rangesBruecheDict = {}
    zahlenAngaben_mehrere = list(set(zahlenAngaben_mehrere))
    if len(zahlenAngaben_mehrere) > 0:
        zahlenAngaben_mehrereStr = ",".join(zahlenAngaben_mehrere)
        zahlenReiheKeineWteiler = copy(zahlenAngaben_mehrereStr)
        if i18n.befehle2["w"] in stext or i18n.befehle2["teiler"] in stext:
            zahlenAngaben_mehrereStr = ",".join(
                [
                    str(zahl)
                    for zahl in BereichToNumbers2(
                        ",".join(
                            [
                                str(z).split("+")[0]
                                for z in zahlenReiheKeineWteiler.split(",")
                            ]
                        ),
                        False,
                        0,
                    )
                ]
            )
            c: str = ",".join(teiler(zahlenAngaben_mehrereStr)[0])
            if len(zahlenReiheKeineWteiler) > 1:
                c += "," + zahlenReiheKeineWteiler
        else:
            c = zahlenAngaben_mehrereStr

    try:
        zahlenReiheKeineWteiler
    except (UnboundLocalError, NameError):
        zahlenReiheKeineWteiler = ""
    return (
        bruch_GanzZahlReziproke,
        c,
        zahlenReiheKeineWteiler,
        fullBlockIsZahlenbereichAndBruch,
        rangesBruecheDict,
        len(zahlenAngaben_) > 0 or EsGabzahlenAngaben,
        rangesBruecheDictReverse,
        stext,
    )


def PromptVonGrosserAusgabeSonderBefehlAusgaben(loggingSwitch, stext, text, warBefehl):
    if len(stext) > 0 and stext[0] in ("shell"):
        warBefehl = True
        try:
            process = subprocess.Popen([*stext[1:]])
            process.wait()
        except:
            pass
    if len(stext) > 0 and "python" == stext[0]:
        warBefehl = True
        try:
            process = subprocess.Popen(["python3", "-c", " ".join(stext[1:])])
            process.wait()
        except:
            pass
    if len(stext) > 0 and "math" == stext[0]:
        warBefehl = True
        for st in "".join(stext[1:2]).split(","):
            try:
                process = subprocess.Popen(["python3", "-c", "print(" + st + ")"])
                process.wait()
            except:
                pass
    stext = text.split()
    if "loggen" in stext:
        warBefehl = True
        loggingSwitch = True
    elif "nichtloggen" in stext:
        warBefehl = True
        loggingSwitch = False
    return loggingSwitch, warBefehl


def promptVorbereitungGrosseAusgabe(
    ketten, platzhalter, promptMode, promptMode2, promptModeLast, text, textDazu0
):
    if text is not None:
        stext: list = text.split()
    else:
        stext: list = []
    ketten = []
    # AusgabeSelektiv = 5
    ifKurzKurz = False
    if len(stext) > 0:
        textDazu: list = []
        s_2: list

        ifKurzKurz, stext = stextFromKleinKleinKleinBefehl(
            ifKurzKurz, promptMode2, stext, textDazu
        )
    if stext is not None:
        nstextnum: list = []
        for astext in stext:
            if astext.isdecimal():
                nstextnum += [int(astext)]
        if len(nstextnum) > 0:
            maxNum = max(nstextnum)
        else:
            maxNum = 1024
    zahlenBereichNeu: map = {}
    zahlenBereichNeu1: map = {}
    for swort in stext:
        try:
            zahlenBereichNeu1[bool(isZeilenAngabe(swort))] += [swort]
        except KeyError:
            zahlenBereichNeu1[bool(isZeilenAngabe(swort))] = [swort]
    for key, value in zahlenBereichNeu1.items():
        zahlenBereichNeu[key] = ",".join(value)

    zahlenBereichMatch = tuple(zahlenBereichNeu.keys())
    if (
        promptMode2 == PromptModus.AusgabeSelektiv
        and promptModeLast == PromptModus.normal
    ):
        stext = textDazu0 + stext
    if (
        promptMode == PromptModus.normal
        and len(platzhalter) > 1
        and platzhalter[:4] == "reta"
        # and not any([("--vorhervonausschnitt" in a or "--vielfachevonzahlen" in a) for a in stext])
        and any(zahlenBereichMatch)
        and zahlenBereichMatch.count(True) == 1
    ):
        zeilenn = False
        woerterToDel = []
        for i, wort in enumerate(stext):
            if len(wort) > 1 and wort[0] == "-" and wort[1] != "-":
                zeilenn = False
            if zeilenn is True or wort == zahlenBereichNeu[True]:
                woerterToDel += [i]
            if wort == "-" + i18n.hauptForNeben["zeilen"]:
                zeilenn = True
                woerterToDel += [i]
        stextDict = {i: swort for i, swort in enumerate(stext)}
        for todel in woerterToDel:
            del stextDict[todel]
        stext = list(stextDict.values())

        if len({i18n.befehle2["w"], i18n.befehle2["teiler"]} & set(stext)) > 0:
            # print(zahlenBereichNeu[True])
            BereichMenge = BereichToNumbers2(zahlenBereichNeu[True], False, 0)
            BereichMengeNeu = teiler(",".join([str(b) for b in BereichMenge]))[1]
            zahlenBereichNeu[True] = ""
            for a in BereichMengeNeu:
                zahlenBereichNeu[True] += str(a) + ","
            zahlenBereichNeu[True] = zahlenBereichNeu[True][:-1]

            try:
                stext.remove(i18n.befehle2["w"])
            except:
                pass
            try:
                stext.remove(i18n.befehle2["teiler"])
            except:
                pass

        if len({i18n.befehle2["v"], i18n.befehle2["vielfache"]} & set(stext)) == 0:
            stext += ["-zeilen", "--vorhervonausschnitt=" + zahlenBereichNeu[True]]

        else:
            # stext += ["-zeilen", "--vorhervonausschnitt=" + zahlenBereichNeu[True]]
            stext += [
                "-zeilen",
                "--vielfachevonzahlen=" + zahlenBereichNeu[True],
            ]
            try:
                stext.remove(i18n.befehle2["v"])
            except:
                pass
            try:
                stext.remove(i18n.befehle2["vielfache"])
            except:
                pass
    IsPureOnlyReTaCmd: bool = len(stext) > 0 and stext[0] == "reta"
    brueche = []
    zahlenAngaben_ = []
    c = ""
    if len(set(stext) & befehleBeenden) > 0:
        stext = [tuple(befehleBeenden)[0]]
    replacements = i18nRP.replacements
    # replacements = {
    #    i18n.befehle2["e"]: i18n.befehle2["keineEinZeichenZeilenPlusKeineAusgabeWelcherBefehlEsWar"],
    #    i18n.befehle2["a"]: i18n.befehle2["absicht"],
    #    "u": "universum",
    #    "t": i18n.befehle2["thomas"],
    #    "r": i18n.befehle2["richtung"],
    #    i18n.befehle2["v"]: i18n.befehle2["vielfache"],
    #    "h": "help",
    #    i18n.befehle2["w"]: i18n.befehle2["teiler"],
    #    "S": "BefehlSpeichernDanach",
    #    "s": "BpromptMode = PromptModus.speichernefehlSpeichernDavor",
    #    i18n.befehle2["l"]: "BefehlSpeicherungLöschen",
    #    i18n.befehle2["o"]: "BefehlSpeicherungAusgeben",
    # }
    for i, token in enumerate(stext):
        try:
            stext[i] = replacements[token]
        except KeyError:
            pass
    if stext[:1] != ["reta"]:
        stext = list(set(stext))
    return (
        IsPureOnlyReTaCmd,
        brueche,
        c,
        ketten,
        maxNum,
        stext,
        zahlenAngaben_,
        ifKurzKurz,
    )


def PromptAllesVorGroesserSchleife():
    global promptMode2, textDazu0, befehleBeenden
    # pp1 = pprint.PrettyPrinter(indent=2)
    # pp = pp1.pprint

    if "-" + i18nRP.retaPromptParameter["vi"] not in sys.argv:
        retaPromptHilfe()
    if "-" + i18nRP.retaPromptParameter["log"] in sys.argv:
        loggingSwitch = True
    else:
        loggingSwitch = False
    if ("-" + i18nRP.retaPromptParameter["h"] in sys.argv) or (
        "-" + i18nRP.retaPromptParameter["help"] in sys.argv
    ):
        print(i18nRP.helptext)
        # print(
        #    """Erlaubte Parameter sind
        #    -vi für vi mode statt emacs mode,
        #    -log, um Logging zu aktivieren,
        #    -debug, um Debugging-Log-Ausgabe zu aktivieren. Das ist nur für Entwickler gedacht.
        #    -befehl bewirkt, dass bis zum letzten Programmparameter retaPrompt Befehl nur ein RetaPrompt-Befehl ausgeführt wird.
        #    -e bewirkt, dass bei allen Befehlen das 'e' Kommando bzw. 'keineEinZeichenZeilenPlusKeineAusgabeWelcherBefehlEsWar' jedes mal verwendet wird - außer wenn der erste Befehl reta war, weil dieser anders funktioniert """
        # )
        exit()
    if "-" + i18nRP.retaPromptParameter["debug"] in sys.argv:
        retaProgram.propInfoLog = True
        if "-" + i18nRP.retaPromptParameter["e"] not in sys.argv:
            alxp("Debug Log aktiviert.")

    if "-" + i18nRP.retaPromptParameter["befehl"] in sys.argv:
        von = "-" + sys.argv.index(i18nRP.retaPromptParameter["befehl"]) + 1
        nurEinBefehl = sys.argv[von:]
    else:
        nurEinBefehl = []
    if "-" + i18nRP.retaPromptParameter["e"] in sys.argv:
        alxp("Debug Log aktiviert.")
        immerEbefehlJa = True
    else:
        immerEbefehlJa = False
    startpunkt1 = NestedCompleter(
        {a: None for a in befehle},
        {},
        ComplSitua.retaAnfang,
        "",
        {
            **{"reta": ComplSitua.retaAnfang},
            **{a: ComplSitua.befehleNichtReta for a in befehle2},
        },
    )
    text: Optional[str] = None

    promptMode = PromptModus.normal
    promptMode2 = PromptModus.normal
    warBefehl: bool
    platzhalter = ""
    ketten = []
    text = ""
    promptDavorDict = defaultdict(lambda: ">")
    promptDavorDict[PromptModus.speichern] = "was speichern>"
    promptDavorDict[PromptModus.loeschenSelect] = "was löschen>"
    nochAusageben = ""
    textDazu0 = []
    return (
        befehleBeenden,
        ketten,
        loggingSwitch,
        nochAusageben,
        platzhalter,
        promptDavorDict,
        promptMode,
        startpunkt1,
        text,
        nurEinBefehl,
        immerEbefehlJa,
    )


def PromptLoescheVorSpeicherungBefehle(platzhalter, promptMode, text):
    global promptMode2, textDazu0
    text = str(text).strip()
    s_text = text.split()
    zuloeschen = text
    loeschbares1 = {i + 1: a for i, a in enumerate(platzhalter.split())}
    loeschbares2 = {a: i + 1 for i, a in enumerate(platzhalter.split())}
    flag = False
    if isZeilenAngabe(zuloeschen):
        if zuloeschen not in loeschbares2.keys():
            zuloeschen2 = BereichToNumbers2(zuloeschen, False, 0)
            for todel in zuloeschen2:
                try:
                    del loeschbares1[todel]
                except:
                    pass
            platzhalter = " ".join(loeschbares1.values())
        else:
            flag = True
    else:
        flag = True
    if flag:
        for wort in s_text:
            try:
                del loeschbares2[wort]
            except:
                pass
        platzhalter = " ".join(loeschbares2.keys())
    promptMode = PromptModus.normal
    if len(platzhalter.strip()) == 0:
        promptMode2 = PromptModus.normal
        textDazu0 = []
    textDazu0 = platzhalter.split()
    return platzhalter, promptMode, text


def promptSpeicherungB(nochAusageben, platzhalter, promptMode, text):
    if promptMode == PromptModus.speicherungAusgaben:
        text = platzhalter
    elif promptMode == PromptModus.speicherungAusgabenMitZusatz:
        text = platzhalter + " " + nochAusageben
    return text


def promptSpeicherungA(ketten, platzhalter, promptMode, text):
    if promptMode == PromptModus.speichern:
        ketten, platzhalter, text = speichern(ketten, platzhalter, text)
    return ketten, platzhalter, text


def promptInput(
    loggingSwitch,
    platzhalter,
    promptDavorDict,
    promptMode,
    startpunkt1,
    text,
    nurEinBefehl,
    immerEbefehlJa,
):

    if len(nurEinBefehl) == 0:
        session = newSession(loggingSwitch)
        try:
            befehlDavor = text
            text = session.prompt(
                # print_formatted_text("Enter HTML: ", sep="", end=""), completer=html_completer
                # ">",
                [("class:bla", promptDavorDict[promptMode])],
                # completer=NestedCompleter.from_nested_dict(
                #    startpunkt, notParameterValues=notParameterValues
                # ),
                completer=startpunkt1
                if not promptMode == PromptModus.loeschenSelect
                else None,
                wrap_lines=True,
                complete_while_typing=True,
                vi_mode=True if "-vi" in sys.argv else False,
                style=Style.from_dict({"bla": "#0000ff bg:#ffff00"})
                if loggingSwitch
                else Style.from_dict({"bla": "#0000ff bg:#ff0000"}),
                # placeholder="reta",
                placeholder=platzhalter,
            )
            text: str = str(text).strip()
            if immerEbefehlJa and text[:4] != "reta":
                textE = [
                    i18n.befehle2[
                        "keineEinZeichenZeilenPlusKeineAusgabeWelcherBefehlEsWar"
                    ]
                ]
            else:
                textE = []
        except KeyboardInterrupt:
            sys.exit()

    else:
        text = " ".join(nurEinBefehl)
        textE = []
        befehlDavor = ""
    return befehlDavor, text, textE


if __name__ == "__main__":
    PromptScope()


def start():
    PromptScope()
