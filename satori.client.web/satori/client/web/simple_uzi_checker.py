# All lines starting with #@ will be treated as checker description XML

#@<checker name="Simple UZI Checker">
#@      <input>
#@              <value name="timelimit" description="Time limit" required="true"/>
#@              <value name="memlimit" description="Memory limit (kbytes)" required="true" default="8192"/>
#@              <file name="generator" description="Test generator" required="false"/>
#@              <value name="gendata" description="Generator data" required="false"/>
#@              <file name="inputfile" description="Input file" required="false"/>
#@              <file name="outputfile" description="Output/hint file" required="false"/>
#@              <file name="specialchecker" description="Specific checker" required="false"/>
#@      </input>
#@</checker>
