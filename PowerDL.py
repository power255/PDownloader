# -*- coding: utf-8 -*- 
#
#source code  https://github.com/volans/paxel/blob/master/paxel.py
#
# 
#
 
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import threading
import os
import sys
import datetime
import time
import io
import gzip
import base64
import math

VERSION="beta 0.0.1"

#Define  downloaded size of the file by one time,here 16 kb
ONEPIECE=16384*8
 
class MutiDL(threading.Thread):
    """Muti_thread download lib,use gzip to read gzipped file."""
    def __init__(self,url,tmpfname,range,referer=None):
        """Add HEADER"""
        threading.Thread.__init__(self)
        self.url=url
        self.tmpfname=tmpfname
        self.range=range
        self.host=self.url.split('/')[2]
        if referer==None:
            self.referer="http://%s"%self.host
        else:
            self.referer=referer
        self.downloaded=0
        
                        
    def readme(self,data):
        '''Read gzip ,if not a gzip file,return itself.'''
        try:
            source= io.StringIO(data)
            gzipper = gzip.GzipFile(fileobj=source)
            html=gzipper.read()
            return html
        except:
            return data
 
    def run(self):
        '''Worker.'''
        self.OnePiece=ONEPIECE
        while True:
            try:
                self.downloaded=os.path.getsize(self.tmpfname)
            except OSError:
                self.downloaded=0
            range0= int(float(self.range[0]))
            range1= int(float(self.range[1]))
            if self.downloaded >= ( range1 - range0):
                break
            sp=range0 +self.downloaded
            if range1 <=self.OnePiece:
                ep=range1
            elif ( range1 -range0 - self.downloaded )<self.OnePiece:
                ep=range1
            else:
                ep=self.OnePiece-1+sp
            rg="bytes=%s-%s"%(str(sp),str(ep))
            # self.headers={"Host":self.host,
            #             "Connection":" keep-alive",
            #             "Referer":self.referer,
            #             "Accept":" */*",
            #             "User-Agent":" Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.98 Safari/534.13",
            #             "Accept-Encoding":" gzip,deflate",
            #             "Accept-Language":" zh-CN,zh;q=0.8",
            #             "Accept-Charset":" GBK,utf-8;q=0.7,*;q=0.3",
            #             "Range":rg}
            self.headers={"Host":self.host,
                        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0",
                        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                        "Accept-Encoding":"gzip, deflate",
                        "Upgrade-Insecure-Requests":"1",
                        "Connection":" keep-alive",
                        "Referer":self.referer,
                        "Accept-Charset":" GBK,utf-8;q=0.7,*;q=0.3",
                        "Range":rg}
            req=urllib.request.Request(self.url,None,self.headers)
            
            
            opener = urllib.request.build_opener(  )
            urllib.request.install_opener( opener )

            r=urllib.request.urlopen(req)
            data=self.readme(r.read())
            f=open(self.tmpfname,"ab+")
            f.write(data)
            f.close()
            self.downloaded+=len(data)
class PowerDF():
    '''Input the file link,filename, block numbers,and the Referer ;Return value rDownloaded,rProcess for reportHoook function.'''
    def __init__(self,url,outfname=None,block=0,referer=None):
        print('url'+url)
        print('outfname'+outfname)
        self.url=self.translink(url)
        if outfname==None:
            self.outfname=self.url.split("/")[-1]
        else:
            self.outfname=outfname
        self.blocknum=block
        if referer==None:
            self.referer="http://%s"%self.url.split("/")[2]
        else:
            self.referer=referer
        self.rFilename=outfname
        self.rFilesize=0
        self.rDownloaded=0
        self.rProcess=0.00
        self.get()
    def translink(self,url):
        '''Tranlate the links to normal link;Surpport Xunlei,QQdl,Flashget,
        fs2you.'''
        url.lower()
        if url.startswith('flashget://'):
            realurl=url.split('//')[1].split('&')[0]
            realurl=base64.decodestring(realurl)
            realurl=realurl.split('[FLASHGET]')[1].split('[FLASHGET]')[0]
        elif url.startswith('qqdl://'):
            realurl=url.split('//')[1]
            realurl=base64.decodestring(realurl)
        elif url.startswith('fs2you://'):
            tmpurl=url.split('//')[1]
            tmpurl=base64.decodestring(tmpurl)
            realurl=tmpurl.split('|')[0]
            tmpfilename=tmpurl.split('|')[-1]
            realurl="http://"+"/".join(realurl.split('/')[:-1])+"/"+tmpfilename
        elif url.startswith('thunder://'):
            tmpurl=url.split('//')[1]
            realurl=base64.decodestring(tmpurl)
            realurl=realurl[2:][:-2]      
        else:
            realurl=url
        return realurl
 
    def GetFileSize(self,url):
        '''Read the file size,only receive 11 bytes responses.'''
        hd={"Range":"bytes=0-10",
            "Referer":self.referer}
        req=urllib.request.Request(url,None,hd)
 
        try:   
            opener = urllib.request.build_opener(  )
            urllib.request.install_opener( opener )
            r=urllib.request.urlopen(req)
        except urllib.error.URLError:
            print("URLError:please check your network..sys will exit...")
            sys.exit(0)
         
        headers=r.getheaders()
        length=0
        for head in headers:
            head="".join(head)
            if head.lower().find("location")!=-1:
                print("Resource removed,server returns 300+ status code....")
                sys.exit(0)
            if head.lower().find("content-range")!=-1:
                length=int(head.split("/")[-1].strip())
        self.rFilesize=length
        return length
    def SplitBlock(self,filesize,block):
        '''Split the file by block number,return a range,splice of the file'''
        zrange=[]
        onepiece=filesize/block
        for i in range(block-1):
            zrange.append([str(i*onepiece),str((i+1)*onepiece-1)])
        zrange.append([str((block-1)*onepiece),str(filesize-1)])
        
        return zrange
    def isAlive(self,tasks):
        for task in tasks:
            if task.isAlive():
                return True
        return False
    def get(self):
        '''Main function of DownLoad'''
        starttime=datetime.datetime.now() 
        fsize=self.GetFileSize(self.url)
        fnum=math.ceil(fsize/ONEPIECE)
        if self.blocknum ==0 :
            if fnum<16:
                self.blocknum=fnum
            else:
                self.blocknum=16
        else:
            if fsize/self.blocknum<=ONEPIECE:self.blocknum=1#For small file,say less than ONEPIECE 16384*8,use only one thread to download
 
        prange=self.SplitBlock(fsize,self.blocknum)
        
        tmpfilename=[]
        for i in range(self.blocknum):
            tmpfilename.append("%s_tmp_%d.tmp"%(self.outfname,i))
        tasks=[]
        for i in range(self.blocknum):
            t=MutiDL(self.url,tmpfilename[i],prange[i])
            t.setDaemon(True)
            tasks.append(t)
        for ts in tasks:
            ts.start()
        
        time.sleep(3)       
        while self.isAlive(tasks):
            self.rDownloaded=sum([t.downloaded for t in tasks])
            self.rProcess=self.rDownloaded/float(self.rFilesize)*100
            time.sleep(0.5)
        fileH=open(self.outfname,"wb+")
        for tmpfile in tmpfilename:
            f=open(tmpfile,"rb")
            fileH.write(f.read())
            f.close()
            try:
                os.remove(tmpfile)
            except:
                pass
        fileH.close()
        endtime = datetime.datetime.now() 
        print( 'start  %s end  %s   time span  %s' % ( starttime , endtime ,endtime - starttime ))
 

        
if __name__=="__main__":
    # dstart = datetime.datetime.now() 
    # print(dstart)
    # link="https://sm.myapp.com/original/im/QQ9.0.2-9.0.2.23490.exe"
    # block=12
    # p=PowerDL(link,None,block)
    # p.get()
    # dend = datetime.datetime.now() 
    # print(dend)
    # print(" time span " , dend-dstart) 
    url = "http://mirrors.163.com/centos/7/isos/x86_64/CentOS-7-x86_64-DVD-1708.iso"
    url = "http://mirrors.163.com/centos/7/isos/x86_64/CentOS-7-x86_64-DVD-1804.iso"
    output = 'c://CentOS-7-x86_64-DVD-1804.iso'
    p=PowerDF(url, output,30,None)