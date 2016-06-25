import gzip
import csv
import scipy.stats

time = []
price = []
volume = []
#daily number of volume buckets
numbuckets = 50

#time by minutes from midnight, price, volume
def time_price_vol_data(time, price, volume):
    zipped = gzip.open('SPY2010-05-06.gz', 'r')
    #zipped = open('test_data.txt', 'r')
    reader = csv.reader(zipped)
    for row in reader:
        hour = float(row[1][:-4])
        minute = float(row[1][-4:-2])
        time.append(float((hour*60) + minute))
        price.append(float(row[7]))
        volume.append(float(row[6]))
    zipped.close()

timebar = []  
delta_pi=[] 
Vi_list = []   
def stand_dev(time, volume, price, delta_pi, Vi_list, timebar):
    count = 0
    Vtot = 0

    #count trades for the day    
    while True:
        try: 
            Vtot += volume[count]
            count +=1
        except:
            break

    #list of Vi and deltaPi 
    #1-minute time bars, for example 4:30:00 <= t < 4:31:00   
    count = 0
    while True:
        try:
            if time[count] == time[count+1]:
                V_i = 0
                price1 = price[count] 
                times = time[count]    
                while time[count] == time[count+1]:
                    V_i += volume[count]
                    count+=1
                Vi_list.append(V_i+volume[count])
                delta_pi.append(price[count] - price1)
                timebar.append(times)
                count+=1 
                V_i = 0
                price1 = price[count]
            else:
                Vi_list.append(volume[count])
                delta_pi.append(0.0)
                timebar.append(time[count])
                count+=1
        except:
            Vi_list.append(V_i+volume[count])
            delta_pi.append(price[count] - price1)
            timebar.append(time[count])
            break            
    #weighted average deltaPi
    mu = 0
    count = 0
    while True:
        try:
            mu += (Vi_list[count]) * (delta_pi[count])
            count+=1
        except:
            break
    mu = mu/Vtot
    #calc standard deviation
    sigma = 0
    count = 0
    while True:
        try:
            sigma += (Vi_list[count]) * ((delta_pi[count] - mu)**2)
            count+=1
        except:
            break
    return (Vtot, (sigma/Vtot)**(0.5))

z=[]    
def findZ(z, stDev, delta_pi):
    count = 0
    while True:
        try:
            z.append(scipy.stats.norm.cdf(delta_pi[count]/stDev))
            count+=1
        except:
            break     

accumvol = []             
def accumulatedvolume(accumvol, Vi_list):
    count = 0
    x = 0
    volsofar = 0
    while True:
        try:
            while x <= count:
                volsofar += Vi_list[x]
                x+=1
            accumvol.append(volsofar)
            count+=1
        except:
            break

bucketnum = [] 
#divide times, price changes, volume into numbered buckets           
def volbuckets(Vtot, numbuckets, accumvol, timebar, delta_pi, Vi_list, z, bucketnum):
    V = int(Vtot/numbuckets)
    num = 1
    count = 0
    while num*V <= Vtot:
        try:
            if accumvol[count] <= num*V:
                bucketnum.append(num)
                count+=1
            else:
                timebar.insert(count+1, timebar[count])
                delta_pi.insert(count+1, delta_pi[count])
                Vi = Vi_list[count]
                Vi_list[count] = num*V - accumvol[count-1]
                Vi_list.insert(count+1, Vi - (num*V - accumvol[count-1]))
                accumvol[count] = accumvol[count-1] + Vi_list[count]
                accumvol.insert(count+1, Vi_list[count+1]+accumvol[count])
                z.insert(count+1, z[count])
                bucketnum.append(num)
                count+=1
                num+=1
        except:
            break

volbuy = []
volsell = []  
orderimbal_bucketnum = []
orderimbal = []
inittime = []
fintime = []
agbuy = []
agsell = []

#calculate the order imbalance for every bucket          
def orderimbalance(Vi_list, z, bucketnum, volbuy, volsell, orderimbal_bucketnum, timebar, orderimbal, agbuy, agsell, inittime, fintime):
    count = 0
    while True:
        try:
            volbuy.append(Vi_list[count]*z[count])
            volsell.append(Vi_list[count]*(1-z[count]))
            count+=1
        except:
            break
    count = 0    
    while True:
        try:
            if bucketnum[count] == bucketnum[count+1]:
                buy = 0
                sell = 0
                time1 = timebar[count] 
                num = bucketnum[count]    
                while bucketnum[count] == bucketnum[count+1]:
                    buy += volbuy[count]
                    sell += volsell[count]
                    count+=1
                agbuy.append(buy+volbuy[count])
                agsell.append(sell+volsell[count])
                orderimbal.append(abs((buy+volbuy[count])-(sell+volsell[count])))
                inittime.append(time1+1)
                fintime.append(timebar[count]+1)
                orderimbal_bucketnum.append(num)
                count+=1 
                buy = 0
                sell = 0
                time1 = timebar[count]
            else:
                agbuy.append(volbuy[count])
                agsell.append(volsell[count])
                orderimbal.append(abs((volbuy[count])-(volsell[count])))
                inittime.append(time1+1)
                fintime.append(timebar[count]+1)
                orderimbal_bucketnum.append(bucketnum[count])
                count+=1
        except:
            agbuy.append(buy+volbuy[count])
            agsell.append(sell+volsell[count])
            orderimbal.append(abs((buy+volbuy[count])-(sell+volsell[count])))
            inittime.append(time1+1)
            fintime.append(timebar[count]+1)
            orderimbal_bucketnum.append(bucketnum[count])
            break   
             
             
 
            
            
time_price_vol_data(time, price, volume)
Vsig = stand_dev(time, volume, price, delta_pi, Vi_list, timebar)
Vtot = Vsig[0]
stDev = Vsig[1]  
findZ(z, stDev, delta_pi)

print timebar      
print delta_pi
print Vi_list

accumulatedvolume(accumvol, Vi_list)
volbuckets(Vtot, numbuckets, accumvol, timebar, delta_pi, Vi_list, z, bucketnum)
orderimbalance(Vi_list, z, bucketnum, volbuy, volsell, orderimbal_bucketnum, timebar, orderimbal, agbuy, agsell, inittime, fintime)
 
print Vtot 
print stDev 
print '\n'
 
print timebar      
print delta_pi
print Vi_list
print accumvol 
print bucketnum 
print z  
print volbuy
print volsell                       
print '\n'

print orderimbal_bucketnum
print agbuy
print agsell
print orderimbal
print inittime
print fintime
print '\n'

print "done"


            
            
            