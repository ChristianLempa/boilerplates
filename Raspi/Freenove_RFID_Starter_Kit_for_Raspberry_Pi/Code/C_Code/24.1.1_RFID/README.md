RC522
=====
#BLOCK Select
1k S50 Mifare 1 card has 1kbytes, 16 sectors and 64 blocks,
Auth with Block 0x00 will be able to access block 0x00-0x03
#Read Example
Check
Select card
AUTH 0x00 with key A or Key B
Read 0x00,0x01,0x02,0x03
Halt

#Write Example
Check
Select card
Auth 0x00 with key A
Write 0x01 with your data
Halt