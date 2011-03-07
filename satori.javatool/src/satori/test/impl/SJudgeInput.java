package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SException;
import satori.common.SInput;
import satori.metadata.SJudge;

public class SJudgeInput implements SInput<SBlob> {
	private final STestImpl test;
	
	public SJudgeInput(STestImpl test) { this.test = test; }
	
	@Override public SBlob get() {
		SJudge judge = test.getJudge();
		return judge != null ? judge.getBlob() : null;
	}
	@Override public String getDescription() { return "Judge file"; }
	@Override public boolean isValid() { return test.getJudge() != null; }
	@Override public void set(SBlob data) throws SException { test.setJudge(data); }
}
