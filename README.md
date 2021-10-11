# cash
A cash program for a bars and restaurants

![image](https://user-images.githubusercontent.com/19941550/54961024-68306400-4f5f-11e9-99c1-14d9b37412b2.png)

### Tables system

![image](https://user-images.githubusercontent.com/19941550/56685264-d76db500-66d1-11e9-84f6-e5b121d38eb3.png)

### Insert partner payments

![image](https://user-images.githubusercontent.com/19941550/56400573-e4635200-6254-11e9-8a91-4bc6447478da.png)

### Consult sells!

![image](https://user-images.githubusercontent.com/19941550/56685456-4a772b80-66d2-11e9-8179-5d86b19adf2c.png)

### How to install

- Get the dist package and install via next next.
- Go to the installation dir and set the configs in`./config/config.cfg` like CIF, Name...
- Execute `cash.exe` and enjoy

### How to migrate version

- Get the installation dir and copy `config` dir.
- Copy db located in Userprofile named `cash.db` 
- Unninstall old version and install the new
- Move `configs` copied folder on installation dir

#### On py3.9

`pip install --upgrade cx-Freeze`

- Clone `https://github.com/francescpuig7/InvoiceGenerator/archive/master.zip'`
- cd InvoiceGenerator
- `pip install -e .`

`python setup.py build`
`python setup.py bdist_msi`
:warning: on windows, copy&paste installation windows dir files

#### On a Win10 py3.7 cx-freeze install:

https://github.com/anthony-tuininga/cx_Freeze/issues/407#issuecomment-453035642

`pip install --upgrade git+https://github.com/anthony-tuininga/cx_Freeze.git@master`
on cmd execute: `cxfreeze-postinstall`

`python setup.py build`
`python setup.py bdist_msi`
