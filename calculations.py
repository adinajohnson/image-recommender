from matplotlib import pyplot as plt

x = [0.95, 0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25, 0.15, 0.05, 0.005]
y = [0.06803894018211298, 0.05076580510758769, 0.042702677871513724, 0.03622041235348365, 0.03019305324135719,
     0.024379151464841948, 0.01880556704924757, 0.013316691147936424, 0.007940728393981031, 0.0026280843117982835,
     0.00026210888753017397]

plt.plot(x, y)
plt.title('The effect of the value of d on the standard deviation of word scores')
plt.xlabel('value of d')
plt.ylabel('standard deviation of scores')
plt.show()