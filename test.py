
bill=open('data/bill_id','r+')
billid=int(bill.read())
bill.seek(0)
bill.write(str(billid+1))