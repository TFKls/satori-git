package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SInput;
import satori.common.SException;

public class SJudgeInput implements SInput<SBlob> {
	private final STestImpl test;
	
	public SJudgeInput(STestImpl test) { this.test = test; }
	
	@Override public SBlob get() { return test.getJudge(); }
	@Override public String getDescription() { return "Judge file"; }
	@Override public boolean isValid() { return test.getJudge() != null; }
	@Override public void set(SBlob data) throws SException { test.setJudge(data); }
}
