
# ICD9 Diagnostic Code Helper Utility
A helper utility that offers fast lookup of ICD9-CM V32 (2015) codes, 
complete with the entire hierarchy.

 
## Why does this utility exist?
ICD9-CMS extends the original (already outdated) ICD9 code standard. 
 
The billable ICD9 codes are available [here](https://www.cms.gov/Medicare/Coding/ICD9ProviderDiagnosticCodes/codes.html).
However, these flat files lack the non-billable hierarchical relations between codes and the intermediate code descriptions.

For example, the above linked file only contains codes 0010, 0011 and 0019, and not the higher level codes 001 and 001-009.

```
001-009: ntestinal Infectious Diseases
    001:Cholera
        0010:Cholera d/t vib cholerae:Cholera due to vibrio cholerae
        0011:Cholera d/t vib el tor:Cholera due to vibrio cholerae el tor 
        0019:Cholera NOS:Cholera, unspecified
    ...
```

This intermediate non-billable nodes have been scraped from 
[http://www.icd9data.com/2015/Volume1/default.htm](http://www.icd9data.com/2015/Volume1/default.htm)
parsed into the hierarchy and merged with the above using cms.gov billable codes. The hierarchy have been
saved to disk. 


### To install 
```
$ pip install icd9cms
```

### To use
```
>>> from icd9cms.icd9 import search
>>>search('001')
001:Cholera:None
>>> # Codes can be searched for with or without the implied '.'  
>>> search('001.0') == search('0010')
True
>>> # The root node is under the code 'n/a' or None
>>> search('n/a')
n/a:root:None
```

#### Parent / Child  / Siblings Relations
```
>>> code = search('001')
>>> code.parent
001-009:Intestinal Infectious Diseases:None
>>> code.children
>>> code.children
[0010:Cholera d/t vib cholerae:Cholera due to vibrio cholerae, 0011:Cholera d/t vib el tor:Cholera due to vibrio cholerae el tor, 0019:Cholera NOS:Cholera, unspecified]
>>> code.siblings
[002:Typhoid and paratyphoid fevers:None, 003:Other salmonella infections:None, 004:Shigellosis:None, 005:Other food poisoning (bacterial):None, 006:Amebiasis:None, 007:Other protozoal intestinal diseases:None, 008:Intestinal infections due to other organisms:None, 009:Ill-defined intestinal infections:None]
```

#### Collect Billable (Leaf) codes / Is a Code Billable (leaf)
```
>>> code = search('0010')
>>> code.is_leaf
True
>>> leaf_codes = search('001-009').leaves
>>> list(leaf_codes)
[0010:Cholera d/t vib cholerae:Cholera due to vibrio cholerae, 0011:Cholera d/t vib el tor:Cholera due to vibrio cholerae el tor, 0019:Cholera NOS:Cholera, unspecified, 0020:Typhoid fever:Typhoid fever, 0021:Paratyphoid fever a:Paratyphoid fever A, 0022:Paratyphoid fever b:Paratyphoid fever B, 0023:Paratyphoid fever c:Paratyphoid fever C, 0029:Paratyphoid fever NOS:Paratyphoid fever, unspecified, 00320:Local salmonella inf NOS:Localized salmonella infection, unspecified, 00321:Salmonella meningitis:Salmonella meningitis, 00322:Salmonella pneumonia:Salmonella pneumonia, ...
```