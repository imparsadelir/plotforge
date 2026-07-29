import pandas as pd 
import matplotlib.pyplot as plt

df =pd.read_excel('test_data.xlsx')

plt.plot(df['time'], df['temperature'],)
plt.xlabel('Time')
plt.ylabel('Temperature') 
plt.title('Temperature vs Time')  
plt.xlim(0 , )
plt.ylim(0 , )
plt.grid()
plt.show() 
