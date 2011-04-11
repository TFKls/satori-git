package satori.test.impl;

import satori.common.SInput;
import satori.data.SBlob;
import satori.metadata.SJudge;
import satori.task.STaskException;

public class SJudgeInput implements SInput<SBlob> {
	private final STestImpl test;
	
	public SJudgeInput(STestImpl test) { this.test = test; }
	
	@Override public SBlob get() {
		SJudge judge = test.getJudge();
		return judge != null ? judge.getBlob() : null;
	}
	@Override public String getText() {
		SJudge judge = test.getJudge();
		return judge != null ? judge.getName() : null;
	}
	@Override public String getDescription() { return "Judge file"; }
	@Override public boolean isValid() { return test.getJudge() != null; }
	@Override public void set(SBlob data) throws STaskException { test.setJudge(data); }
}
