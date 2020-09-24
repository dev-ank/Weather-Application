import requests
from flask import Flask, render_template, request, session, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from geopy.geocoders import Nominatim
import arrow


app=Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'thisisasecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def get_weather_api_url(lat,lon):
	r=requests.get(f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&%20exclude=minutely&units=metric&appid=8b71baf8166971a8fea34227202ae93a')
	data=r.json()
	return data



class User(db.Model):

	__tablename__='User'

	sno=db.Column(db.Integer,primary_key=True)
	email=db.Column(db.String(50),nullable=False)
	password=db.Column(db.String(50),nullable=False)


class Weather(db.Model):

	__tablename__='Weather'

	sno=db.Column(db.Integer,primary_key=True)
	location=db.Column(db.String(50),nullable=False)
	lat=db.Column(db.String(100),nullable=False)
	lon=db.Column(db.String(100),nullable=False)



class Detail_Weather(db.Model):

	__tablename__='Detail_Weather'

	sno=db.Column(db.Integer,primary_key=True)
	location=db.Column(db.String(50),nullable=False)
	lat=db.Column(db.String(100),nullable=False)
	lon=db.Column(db.String(100),nullable=False)




@app.route('/sort_index')
def sort_index():
	cities=Weather.query.all()

	weather_data=[]

	for city in cities:
		json_data=get_weather_api_url(city.lat,city.lon)
		location=city.location
		location=location.title()

		weather={
			'city':location,
			'temperature':json_data['current']['temp'],
			'description':json_data['current']['weather'][0]['description'],
			'icon':json_data['current']['weather'][0]['icon'],
		}

		weather_data.append(weather)

	return render_template('sort_index.html',weather_data=weather_data)



@app.route('/')
def get_index():

	cities=Weather.query.all()

	weather_data=[]

	for city in cities:
		json_data=get_weather_api_url(city.lat,city.lon)
		location=city.location
		location=location.title()

		weather={
			'city':location,
			'temperature':json_data['current']['temp'],
			'description':json_data['current']['weather'][0]['description'],
			'icon':json_data['current']['weather'][0]['icon'],
		}

		weather_data.append(weather)

	return render_template('index.html',weather_data=weather_data)



@app.route('/',methods=['POST'])
def index():
	err_msg=''
	city=request.form.get('city')

	if city:
		existing_city=Weather.query.filter_by(location=city).first()

		if not existing_city:

			geolocator = Nominatim(user_agent="app")
			location = geolocator.geocode(city)

			
			

			if location:
				lat=location.latitude
				lon=location.longitude
				json_data=get_weather_api_url(lat,lon)

			
				location=city
				location=location.title()
		
				entry=Weather(location=location,lat=lat,lon=lon)
				db.session.add(entry)
				db.session.commit()
			else:
				err_msg='City does not exists!'
			

		else:
			err_msg='City already exist below!'

		
		if err_msg:
			flash(err_msg, 'error')
		else:
			flash('City added Successfully!')

	
		return redirect(url_for('get_index'))

	

@app.route('/delete/<location>')
def delete(location):
	rem=Weather.query.filter_by(location = location).first()
	db.session.delete(rem)
	db.session.commit()

	flash(f'Successfully deleted { location }', 'success')
	return redirect(url_for('get_index'))


@app.route('/login', methods=['GET','POST'])
def login():
	err_msg = ''
	if request.method=="POST":
		email=request.form.get('email')
		password=request.form.get('password')

		exists=db.session.query(User.sno).filter_by(email=email).scalar()

		if exists is not None:

			check=db.session.query(User).filter_by(sno=exists).first()

			if check.email==email and check.password==password:

				if 'userid' in session and session['userid']==exists:
					err_msg = 'User already logged in.'
					return redirect(url_for('dashboard',userid=session['userid']))
				else:
					session['userid']=exists

			else:
				err_msg = 'Incorrect Email or Password!'

		else:
			err_msg = 'Please Sign-In first'


		if err_msg:
				flash(err_msg, 'error')
		else:
			
			return redirect(url_for('dashboard',userid=exists))
		


	return render_template('login.html')



@app.route('/signup', methods=['GET','POST'])
def signup():
	err_msg = ''
	if request.method=="POST":
		email=request.form.get('email')
		password=request.form.get('password')
		cpassword=request.form.get('cpassword')

		if password==cpassword:
			entry=User(email=email,password=password)
			exists = db.session.query(User.sno).filter_by(email=entry.email).scalar()


			if exists is None:
				db.session.add(entry)
				db.session.commit()
			else:
				err_msg = 'User with this email already exists. Please try some other mail-id!'


		else:
			err_msg = 'Password and Confirm Password should be same!'

		

		if err_msg:
			flash(err_msg, 'error')
		else:
			flash('Account added succesfully!')
			return redirect('/login')

	return render_template('signup.html')



@app.route('/dashboard/<string:userid>')
def dashboard(userid):
	cities=Detail_Weather.query.all()

	weather_data=[]

	for city in cities:
		json_data=get_weather_api_url(city.lat,city.lon)
		location=city.location
		location=location.title()

		weather={
			'city':location,
			'time':json_data['current']['dt'],
			'temperature':json_data['current']['temp'],
			'sunrise':json_data['current']['sunrise'],
			'sunset':json_data['current']['sunset'],
			'pressure':json_data['current']['pressure'],
			'humidity':json_data['current']['humidity'],
			'uvi':json_data['current']['uvi'],
			'visibility':json_data['current']['visibility'],
			'feels_like':json_data['current']['feels_like'],
			'wind_speed':json_data['current']['wind_speed'],
			'current_weather':json_data['current']['weather'][0]['main'],
			'icon':json_data['current']['weather'][0]['icon']
			
		}
		weather['time']=arrow.get(weather['time']).to('local').format()
		weather['time']=''.join(list(weather['time'])[11:16])
		

		weather['sunrise']=arrow.get(weather['sunrise']).to('local').format()
		weather['sunrise']=''.join(list(weather['sunrise'])[11:16])
		

		weather['sunset']=arrow.get(weather['sunset']).to('local').format()
		weather['sunset']=''.join(list(weather['sunset'])[11:16])
		weather_data.append(weather)


	return render_template('dashboard.html',weather_data=weather_data)
	
	
@app.route('/delete_details/<location>')
def delete_details(location):
	if location:
		rem=Detail_Weather.query.filter_by(location = location).first()
		db.session.delete(rem)
		db.session.commit()

		flash(f'Successfully deleted { location }', 'success')
	return redirect(url_for('dashboard',userid=session['userid']))



@app.route('/post_details',methods=['POST'])
def post_details():
	err_msg=''
	city=request.form.get('city')

	if city:
		existing_city=Detail_Weather.query.filter_by(location=city).first()

		if not existing_city:

			geolocator = Nominatim(user_agent="app")
			location = geolocator.geocode(city)

			
			

			if location:
				lat=location.latitude
				lon=location.longitude
				json_data=get_weather_api_url(lat,lon)

			
				location=city
				location=location.title()
		
				entry=Detail_Weather(location=location,lat=lat,lon=lon)
				db.session.add(entry)
				db.session.commit()
			else:
				err_msg='City does not exists!'
			

		else:
			err_msg='City already exist below!'

		
		if err_msg:
			flash(err_msg, 'error')
		else:
			flash('City added Successfully!')

	
		return redirect(url_for('dashboard',userid=session['userid']))


@app.route('/logout')
def logout():
	if 'userid':
		session.pop('userid')
		return redirect(url_for('index'))


if __name__=="__main__":
	app.run()