
echo \n
echo #############\n
echo # Python Help\n
echo #############\n
help python

echo \n
echo #############################################################\n
echo # Execute a basic python script (will force exit with code 0)\n
echo #############################################################\n

python
import sys
c = 0
print("Python script seems to work ...")
print("Exiting with code: {}".format(c))
sys.exit(0)
end


echo \n
echo \n
echo #########################################################\n
echo # Something went wrong in python script, for exit code 25\n
echo #########################################################\n
q 25
