import gzip
import csv
import scipy.stats
import matplotlib.pyplot as plt

time = []
price = []
volume = []
#Daily number of volume buckets
numbuckets = 50
#SPY has ~100,000,000 daily vol
V = 100000000/50

#Parse time: minutes from midnight, price, volume
def time_price_vol_data(time, price, volume):
    zipped = gzip.open('SPY2010-04-28.gz', 'r')
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

    #Count trades for the day  
    while True:
        try: 
            Vtot += volume[count]
            count +=1
        except:
            break

    #List of Vi and deltaPi 
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
    #Weighted average of the deltaPi
    mu = 0
    count = 0
    while True:
        try:
            mu += (Vi_list[count]) * (delta_pi[count])
            count+=1
        except:
            break
    mu = mu/Vtot
    #Calculate the standard deviation in the deltaPi
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
#Divide times, price changes, volume into numbered buckets           
def volbuckets(Vtot, V, accumvol, timebar, delta_pi, Vi_list, z, bucketnum):
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
    count = len(bucketnum)
    num = bucketnum[len(bucketnum)-1]
    try:
        if accumvol[count] > num*V:
            while True:
                try:
                    timebar.pop(count)
                    delta_pi.pop(count)
                    Vi_list.pop(count)
                    accumvol.pop(count)
                    z.pop(count)
                except:
                    break
    except:
        pass
                
            

volbuy = []
volsell = []  
orderimbal_bucketnum = []
orderimbal = []
inittime = []
fintime = []
agbuy = []
agsell = []

#Calculate the order imbalance for every bucket     
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
        buy = 0
        sell = 0
        time1 = timebar[count] 
        try:
            if bucketnum[count] == bucketnum[count+1]:
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

vpin=[]
vpin_fintime=[]            
def calcvpin(numbuckets, V, orderimbal, fintime, vpin, vpin_fintime):
    num = 0
    while True:
        try:
            count = 0
            OIag = 0
            while (count + num) < (numbuckets + num):
                OIag+=orderimbal[count+num]
                count+=1
            vpin.append(OIag/(numbuckets*V))
            vpin_fintime.append(fintime[count+num-1])
            num+=1
        except:
            break
            
            
time2 = []
price2 = []

def time_price_data2(time2, price2):
    zipped = gzip.open('SPY2010-04-28.gz', 'r')
    reader = csv.reader(zipped)
    for row in reader:
        hour = float(row[1][:-4])
        minute = float(row[1][-4:-2])
        second = float(row[1][-2:])
        millisec = float(row[2])
        time2.append(hour*60 + minute + second/60 + millisec/60000)
        price2.append(float(row[7]))
    zipped.close()
    
                            
def graph(vpin_fintime, vpin, time2, price2):
    xlabels = []
    xmarks = []
    count = 0
    time = 60*(int(vpin_fintime[0]/60))
    while time <= vpin_fintime[len(vpin_fintime)-1]:
        time = 60*(int(vpin_fintime[0]/60)) + 30*count
        xmarks.append(time)
        hour = str(int(time/60))
        minutenum = int(time%60)
        if minutenum < 10:
            minute = '0' + str(minutenum)
        else:
            minute = str(minutenum)
        xlabels.append(hour+':'+minute)
        count+=1
    print xlabels
    print xmarks
    
    fig, ax1 = plt.subplots()
    plt.xticks(xmarks, xlabels, rotation='vertical')
    ax1.plot(time2, price2, 'b.')
    ax1.set_xlabel('Time') 
    ax1.set_ylabel('Price ($)', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b') 
        
    ax2 = ax1.twinx()
    ax2.plot(vpin_fintime, vpin, 'r.') 
    ax2.set_ylabel('VPIN', color = 'r')
    for tl in ax2.get_yticklabels():
        tl.set_color('r')
    plt.xlim([xmarks[0],vpin_fintime[len(vpin_fintime)-1]])
    plt.title('SPY Price and VPIN on 28 April 2010')
    plt.show()
            
            
time_price_vol_data(time, price, volume)
Vsig = stand_dev(time, volume, price, delta_pi, Vi_list, timebar)
Vtot = Vsig[0]
stDev = Vsig[1]  
findZ(z, stDev, delta_pi)

accumulatedvolume(accumvol, Vi_list)
volbuckets(Vtot, V, accumvol, timebar, delta_pi, Vi_list, z, bucketnum)
orderimbalance(Vi_list, z, bucketnum, volbuy, volsell, orderimbal_bucketnum, timebar, orderimbal, agbuy, agsell, inittime, fintime)
calcvpin(numbuckets, V, orderimbal, fintime, vpin, vpin_fintime)
time_price_data2(time2, price2)
graph(vpin_fintime, vpin, time2, price2)

print vpin
print vpin_fintime
print Vtot



            
            
            
