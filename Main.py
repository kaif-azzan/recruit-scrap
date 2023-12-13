#web scrapping recruitment application that pulls data from several websites and pools them all together to close the gap between the recruiteer and the job seeker

from flask import Flask,render_template,request,session,redirect
import mysql.connector
import requests
from flask_socketio import SocketIO, send

con=mysql.connector.connect(host='localhost',user='root',password='root123',database='coursify')
if con.is_connected:
    print("db connected")
else:
    print("db not connected")

app=Flask(__name__,template_folder='template')
socketio=SocketIO(app,cors_allowed_origins="*")
app.secret_key='xdjshfksd'

@socketio.on("message")
def sendMessage(message):
    send(message, broadcast=True)

@app.route('/',methods=['GET','POST'])
def login():
    if request.method=="POST":
        uname=request.form['uname']
        upass=request.form['pas']   
        cursor=con.cursor()
        cursor.execute("SELECT `username`,`password`,`name`,`role`,`llurl` FROM `member` WHERE `username`=%s and `password`=%s",(uname,upass))
        record=cursor.fetchall()
        cursor.close()
        if record:
            session['logedin']=True
            session['username']=record[0][2]
            session['skills']=''
            session['role']=record[0][3]
            session['llurl']=record[0][4]
            if session['role']=='jobseeker':
                session['status']=1
            else:
                session['status']=0
            return render_template('dashboard.html',username=session['username'],count=session['status'])
        else:
            error='Username or password mismatch'
            return render_template('dashboard.html',error=error)
    else:
        return render_template("dashboard.html")

def letter():
    if request.method=="POST":
        arr=[]
        emaill=request.form['emaill']
        arr.append(emaill)
        return render_template('dashboard.html')

@app.route('/signup',methods=['GET','POST'])
def signup():
        if request.method=="POST":
            uname=request.form['newuname']
            upass=request.form['newpass']
            name=request.form['fname']
            email=request.form['email']
            lll=request.form['lll']
            box1=request.form.get('mycheckbox1')
            box2=request.form.get('mycheckbox2')
            
            if box1=='on' and box2==None or box1==None and box2=='on':
                if box1:
                    role='recruiter'
                else:
                    role='jobseeker'
                cursor=con.cursor()
                cursor.execute("SELECT `username` FROM `member` WHERE `username`=%s",(uname,))
                record=cursor.fetchall()
                cursor.close()
                if record:
                    error='Username already in use, Pick something new'
                    return render_template("signup.html",error=error)
                else:
                    cursor=con.cursor()
                    cursor.execute("SELECT `email` FROM `member` WHERE `email`=%s",(email,))
                    record=cursor.fetchall()
                    cursor.close()
                    if record:
                        error='email already in use'
                        return render_template("signup.html",error=error)
                    else:
                        cursor=con.cursor()
                        cursor.execute("INSERT INTO `member` (`username`, `password`,`name`,`email`,`role`,`llurl`) VALUES (%s,%s,%s,%s,%s,%s)",(uname,upass,name,email,role,lll))
                        con.commit()
                        cursor.close()
                        return render_template('dashboard.html')
            else:
                    error="Please only select one box"
                    return render_template('signup.html',error=error)
        else:
            return render_template('signup.html')

@app.route('/homepage')
def start():

    if session['role']=='jobseeker':

        cursor=con.cursor()
        cursor.execute("select * from `job_seeker`;")
        temp=cursor.fetchall()
        cursor.close()

        return render_template('try2.html',role=session['role'],unm=session['username'],info=temp)
    else:

        cursor=con.cursor()
        cursor.execute("select * from `member` where `name`=%s;",(session['username'],))
        side=cursor.fetchall()
        cursor.close()

        cursor=con.cursor()
        cursor.execute("select * from `basic_info`")
        rows=cursor.fetchall() #rows is in tuple format so we declare first and second to convert them into lists
        cursor.close()

        #begining of conversion to list
        first=[]
        second=[]

        for i in range(len(rows)):
            for j in range(len(rows[i])):
                second.append(rows[i][j])
            first.append(second)
            second=[]

        #end of conversion to list

        if len(session['skills'])>0:
            converted_skills_to_list=session['skills'].split()

            cursor=con.cursor()
            cursor.execute("select `about` from `basic_info`;")
            col=cursor.fetchall()
            cursor.close()

            final=[]

            for j in range(0,len(col)):
                counter=0
                for i in range(0,len(converted_skills_to_list)):
                    if converted_skills_to_list[i] in col[j][0]:
                        counter+=1

                counter=(counter//len(converted_skills_to_list))*100
                final.append(counter)

            for i in range(len(first)):
                first[i].append(final[i])

            value=False
            return render_template('try2.html',reqs=session['skills'],info=first,side=side,value=value)

        else:

            if request.method=='POST':
                 rol=request.form['field1']
                 comp=request.form['field2']
                 api_key = 'icD6s2qWEm5kNuIDuutLkA'
                 headers = {'Authorization': 'Bearer ' + api_key}
                 api_endpoint ='https://nubela.co/proxycurl/api/find/company/role/'
                 params = {
                     'role':rol,
                     'company_name':comp,
                 }
                 response = requests.get(api_endpoint,
                                         params=params,
                                         headers=headers)

                 good=response.json()
                 profile_url=good['linkedin_profile_url']

                 api_endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'
                 linkedin_profile_url = profile_url
                 headers = {'Authorization': 'Bearer ' + api_key}

                 response = requests.get(api_endpoint,params={'url': linkedin_profile_url},headers=headers)

                 good=response.json()

                 name=good['full_name']
                 city=good['city']
                 country=good['country_full_name']
                 about=good['summary']
                 picture=None

                 cursor=con.cursor()
                 cursor.execute("insert into `basic_info` (`name`,`city`,`country`,`about`,`profile_url`) values (%s,%s,%s,%s,%s);",(name,city,country,about,profile_url,))
                 con.commit()
                 cursor.close()
                 return render_template('try2.html',reqs='',info=first,side=side,value=value)
            else:
                value=True
                return render_template('try2.html',reqs='',info=first,side=side,value=value)


@app.route('/skill',methods=['GET','POST'])
def enter():
    
    if request.method=='POST':
        session['skills']=request.form['skills']
        session['country']=request.form['country']
        session['state']=request.form['state']
        return redirect('/homepage')
    else:
        return render_template('skill.html')
    
@app.route('/post',methods=['GET','POST'])
def work():
    if request.method=="POST":
        fir=request.form['first']
        sec=request.form['second']
        thir=request.form['third']
        cursor=con.cursor()
        cursor.execute("INSERT INTO `basic_info` (`name`,`city`,`country`,`about`,`profile_url`) VALUES (%s,%s,%s,%s,%s)",(session['username'],thir,sec,fir,session['llurl']))
        con.commit()
        cursor.close()
        return redirect('/homepage')
    else:
        return render_template('self.html')
@app.route('/del',methods=['GET','POST'])
def deel():
    if request.method=="POST":
        k=request.form['confirm']
        cursor=con.cursor()
        cursor.execute('DELETE FROM `basic_info` WHERE `name` = %s',(session['username']))
        con.commit()
        cursor.close()
        return render_template('del.html')
    else:
        return render_template('del.html')

if __name__=='__main__':
    app.run(debug=True)