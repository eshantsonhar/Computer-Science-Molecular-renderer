#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <sstream>

using namespace std;


namespace Aldehyde {

template<typename DataTypeOne, typename DataTypeTwo>
class Pair {
public:
    struct DataStructure {
        DataTypeOne Key;
        DataTypeTwo Value;
    };
    DataStructure Data;
    Pair(DataTypeOne InitKey, DataTypeTwo InitValue) : Data{InitKey, InitValue} {};
    void ChangeKey(DataTypeOne NewKey) { Data.Key = NewKey; }
    void ChangeValue(DataTypeTwo NewValue) { Data.Value = NewValue; }
    void ChangePair(DataTypeOne NewKey, DataTypeTwo NewValue) {
        Data.Key = NewKey;
        Data.Value = NewValue;
    }
};

// Prefixes
vector<Pair<string, int>> NumberPrefixes = {
    {"meth", 1}, {"eth", 2}, {"prop", 3}, {"but", 4}, {"pent", 5},
    {"hex", 6}, {"hept", 7}, {"oct", 8}, {"non", 9}, {"dec", 10}
};

vector<string> BreakDownString(string Name) {
    string ImmediateString;
    vector<string> StringVector;
    for (char X : Name) {
        if (X != '-') {
            ImmediateString += X;
        } else if (!ImmediateString.empty()) {
            StringVector.push_back(ImmediateString);
            ImmediateString.clear();
        }
    }
    return StringVector;
}

bool containsOnlyNumbersAndCommas(const string& str) {
    if (str.empty()) return false;
    for (char c : str) {
        if (!isdigit(c) && c != ',') return false;
    }
    return true;
}

void FindAndReplaceAll(string& data, const string& match, const string& replace) {
    size_t pos = data.find(match);
    while (pos != string::npos) {
        data.replace(pos, match.size(), replace);
        pos = data.find(match, pos + replace.size());
    }
}

vector<Pair<string, string>> ConvertFromRawLocantToRawPair(const vector<string>& InputLocants) {
    vector<Pair<string, string>> RawLocantPairs;
    Pair<string, string> CurrentPair("", "");
    for (const auto& item : InputLocants) {
        if (containsOnlyNumbersAndCommas(item)) {
            CurrentPair.ChangeKey(item);
        } else {
            CurrentPair.ChangeValue(item);
            RawLocantPairs.push_back(CurrentPair);
            CurrentPair.ChangePair("", "");
        }
    }
    return RawLocantPairs;
}

vector<int> stringToVector(const string& s) {
    vector<int> result;
    stringstream ss(s);
    string segment;
    while (getline(ss, segment, ',')) {
        try {
            if (!segment.empty()) result.push_back(stoi(segment));
        } catch (...) {}
    }
    return result;
}

vector<Pair<vector<int>, string>> ConvertFromRawLocantPairToLocantPair(const vector<Pair<string, string>>& RawLocantPairs) {
    vector<Pair<vector<int>, string>> LocantPairs;
    for (const auto& raw : RawLocantPairs) {
        LocantPairs.push_back({stringToVector(raw.Data.Key), raw.Data.Value});
    }
    return LocantPairs;
}

vector<int> FindParentPrefix(string RawName) {
    vector<int> FoundNumbers;
    string temp = RawName;
    for (auto& prefix : NumberPrefixes) {
        if (temp.find(prefix.Data.Key) != string::npos) {
            FoundNumbers.push_back(prefix.Data.Value);
        }
    }
    return FoundNumbers;
}

// Data Classes
class DoubleBond {
public:
    int type = 2;
    string yfrom, yto;
    vector<string> GetJson() {
        return {"{", "\"bondtype\":\"2\",", "\"yposfrom\":\"" + yfrom + "\",", "\"yposto\":\"" + yto + "\"", "},"};
    }
};

class TripleBond {
public:
    int type = 3;
    string yfrom, yto;
    vector<string> GetJson() {
        return {"{", "\"bondtype\":\"3\",", "\"yposfrom\":\"" + yfrom + "\",", "\"yposto\":\"" + yto + "\"", "},"};
    }
};

class JSONObject {
public:
    string Locant, Atoms;
    vector<string> GetJson() {
        return {"{", "\"locantnumber\":\"" + Locant + "\",", "\"numberofatoms\":\"" + Atoms + "\"", "},"};
    }
};
class AlcoholGroup{
public:
	string Locant;
	vector<string> GetJson() {
        return {"{", "\"locantnumber\":\"" + Locant + "\",", "\"group\":\"alcohol\"" , "},"};
    }
};
class KetoGroup{
public:
	string Locant;
	vector<string> GetJson() {
        return {"{", "\"locantnumber\":\"" + Locant + "\",", "\"group\":\"ketone\"" , "},"};
    }
};
class EpoxyGroup {
public:
    string yfrom, yto;
    vector<string> GetJson() {
        return {"{", "\"group\":\"epoxy\",", "\"yposfrom\":\"" + yfrom + "\",", "\"yposto\":\"" + yto + "\"", "},"};
    }
};
class FluoroGroup{
public:
    string Locant;
	vector<string> GetJson() {
        return {"{", "\"locantnumber\":\"" + Locant + "\",", "\"group\":\"fluoro\"" , "},"};
    }
};
class BromoGroup{
public:
    string Locant;
	vector<string> GetJson() {
        return {"{", "\"locantnumber\":\"" + Locant + "\",", "\"group\":\"bromo\"" , "},"};
    }
};
class IodoGroup{
public:
    string Locant;
	vector<string> GetJson() {
        return {"{", "\"locantnumber\":\"" + Locant + "\",", "\"group\":\"iodo\"" , "},"};
    }
};
class ChloroGroup{
public:
    string Locant;
	vector<string> GetJson() {
        return {"{", "\"locantnumber\":\"" + Locant + "\",", "\"group\":\"chloro\"" , "},"};
    }
};
class AldoGroup{
  public:
    string Locant;
	vector<string> GetJson() {
        return {"{", "\"locantnumber\":\"" + Locant + "\",", "\"group\":\"aldehyde\"" , "},"};
    }  
};
struct GeneralObject {
    int Type = -1; // 0: JSON, 1: Double, 2: Triple, 3: Hydroxy(OH), 4: Ketones(=O), 5: Epoxy, 6: Fluoro, 7: Bromo, 8: Iodo, 9: Chloro, 10: Aldehyde
    JSONObject JSON;
    DoubleBond Double;
    TripleBond Triple;
    AlcoholGroup Alcohol;
	KetoGroup Ketone;
	EpoxyGroup Epoxide;
    FluoroGroup Fluoro;
    BromoGroup Bromo;
    IodoGroup Iodo;
    ChloroGroup Chloro;
    AldoGroup Aldo;
};

vector<GeneralObject> ConvertStringNamesIntoNumberOfCarbonAtomsAndCreateWriteData(vector<int> ParentNums, vector<Pair<vector<int>, string>> LocantPairs) {
    vector<GeneralObject> FinalVector;
    
    for (size_t i = 0; i < LocantPairs.size(); ++i) {
        string val = LocantPairs[i].Data.Value;
        
        if (val.find("ene") != string::npos || val.find("en") != string::npos) {
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 1;
                go.Double.yfrom = to_string(pos);
                go.Double.yto = to_string(pos + 1);
                FinalVector.push_back(go);
            }
        } 
        else if (val.find("yne") != string::npos || val.find("yn") != string::npos) {
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 2;
                go.Triple.yfrom = to_string(pos);
                go.Triple.yto = to_string(pos + 1);
                FinalVector.push_back(go);
            }
        }
        else if (val.find("ol") != string::npos || val.find("hydroxy") != string::npos ){
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 3;
                go.Alcohol.Locant = to_string(pos);
                FinalVector.push_back(go);
            }
        }
		else if (val.find("on") != string::npos || val.find("one") != string::npos ||val.find("keto") != string::npos  ){
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 4;
                go.Ketone.Locant = to_string(pos);
                FinalVector.push_back(go);
            }
        }
        else if (val.find("epoxy") != string::npos || val.find("epox") != string::npos) {
                GeneralObject go; go.Type = 5;
                go.Epoxide.yfrom = to_string(LocantPairs[i].Data.Key[0]);
                go.Epoxide.yto = to_string(LocantPairs[i].Data.Key[0]+1);
                FinalVector.push_back(go);
        } 
        else if (val.find("fluoro") != string::npos){
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 6;
                go.Fluoro.Locant = to_string(pos);
                FinalVector.push_back(go);
            }
        }
        else if (val.find("bromo") != string::npos){
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 7;
                go.Bromo.Locant = to_string(pos);
                FinalVector.push_back(go);
            }
        }
        else if (val.find("iodo") != string::npos){
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 8;
                go.Iodo.Locant = to_string(pos);
                FinalVector.push_back(go);
            }
        }
        else if (val.find("chloro") != string::npos){
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 9;
                go.Chloro.Locant = to_string(pos);
                FinalVector.push_back(go);
            }
        }
        else if (val.find("al") != string::npos ||val.find("formyl") != string::npos || val.find("oxo") != string::npos ){
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 10;
                go.Aldo.Locant = to_string(pos);
                FinalVector.push_back(go);
            }
        }
        else  {
            for (int pos : LocantPairs[i].Data.Key) {
                GeneralObject go; go.Type = 0;
                go.JSON.Locant = to_string(pos);
                go.JSON.Atoms = to_string(ParentNums[i]);
                FinalVector.push_back(go);
            }
        }
    }

    // Add Main Parent
    if (!ParentNums.empty()) {
        GeneralObject mainChain;
        mainChain.Type = 0;
        mainChain.JSON.Locant = "0";
        mainChain.JSON.Atoms = to_string(ParentNums.back());
        FinalVector.push_back(mainChain);
    }

    return FinalVector;
};

void WriteDataToFile(vector<GeneralObject> Data) {
    // clear file before writing lmaop
    ofstream File("output.json", ios::trunc); 
    File << "[" << endl;

    for (int i = 0; i < Data.size(); ++i) {
        vector<string> output;
        if (Data[i].Type == 0) output = Data[i].JSON.GetJson();
        else if (Data[i].Type == 1) output = Data[i].Double.GetJson();
        else if (Data[i].Type == 2) output = Data[i].Triple.GetJson();
        else if (Data[i].Type == 3) output = Data[i].Alcohol.GetJson();
		else if (Data[i].Type == 4) output = Data[i].Ketone.GetJson();
        else if (Data[i].Type == 5) output = Data[i].Epoxide.GetJson();
        else if (Data[i].Type == 6) output = Data[i].Fluoro.GetJson();
        else if (Data[i].Type == 7) output = Data[i].Bromo.GetJson();
        else if (Data[i].Type == 8) output = Data[i].Iodo.GetJson();
        else if (Data[i].Type == 9) output = Data[i].Chloro.GetJson();
        else if (Data[i].Type == 10) output = Data[i].Aldo.GetJson();
        for (int j = 0; j < output.size(); ++j) {
            string line = output[j];
            // if this is the last object AND we are looking at the "}," line
            if (i == Data.size() - 1 && line == "},") {
                File << "}"; // write it without the comma
            } else {
                File << line;
            }
            File << endl;
        }
    }
    File << "]" << endl;
    File.close();
}

void AldehydeParser(string Name){
    Name += "-";

    vector<string> BrokenDown = BreakDownString(Name);
    vector<Pair<string, string>> Locants = ConvertFromRawLocantToRawPair(BrokenDown);
    vector<Pair<vector<int>, string>> RLocants = ConvertFromRawLocantPairToLocantPair(Locants);
    vector<int> Numbers = FindParentPrefix(Name);

    vector<GeneralObject> FinalObjects = ConvertStringNamesIntoNumberOfCarbonAtomsAndCreateWriteData(Numbers, RLocants);
    WriteDataToFile(FinalObjects);
}
};

int main(){
    string Name;
    cin >> Name;
    Aldehyde::AldehydeParser(Name);
	return 0;
};
