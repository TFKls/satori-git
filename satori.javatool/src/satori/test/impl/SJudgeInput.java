package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SData;
import satori.common.SException;

public class SJudgeInput implements SData<SBlob> {
	private final STestImpl test;
	
	public SJudgeInput(STestImpl test) { this.test = test; }
	
	@Override public SBlob get() { return test.getJudge(); }
	@Override public boolean isEnabled() { return true; }
	@Override public boolean isValid() { return true; }
	@Override public void set(SBlob data) throws SException { test.setJudge(data); }
}
