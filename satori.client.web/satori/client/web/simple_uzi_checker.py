# All lines starting with #@ will be treated as checker description XML

#@<checker name="Simple UZI Checker">
#@      <section name="input">
#@              <param type="int" name="timelimit" description="Time limit" required="true" default="10s"/>
#@              <param type="int"  name="memlimit" description="Memory limit" required="true" default="256M"/>
#@              <param type="blob" name="generator" description="Test generator" required="false"/>
#@              <param type="text" name="gendata" description="Generator data" required="false"/>
#@              <param type="blob" name="inputfile" description="Input file" required="false"/>
#@              <param type="blob" name="outputfile" description="Output/hint file" required="false"/>
#@              <param type="blob" name="specialchecker" description="Specific checker" required="false"/>
#@      </section>
#@</checker>
