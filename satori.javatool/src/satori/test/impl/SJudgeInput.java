package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SData;
import satori.common.SException;

public class SJudgeInput implements SData<SBlob> {
	public static enum Status { VALID, INVALID, DISABLED };
	
	private final STestImpl test;
	
	public SJudgeInput(STestImpl test) {
		this.test = test;
	}
	
	@Override public SBlob get() { return test.getJudge(); }
	@Override public void set(SBlob data) throws SException { test.setJudge(data); }
	
	public Status getStatus() { return Status.VALID; }
	
	@Override public boolean isEnabled() { return getStatus() != Status.DISABLED; }
	@Override public boolean isValid() { return getStatus() == Status.VALID; }
}
