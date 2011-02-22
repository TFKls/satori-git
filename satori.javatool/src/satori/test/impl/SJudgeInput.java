package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SData;
import satori.common.SException;

public class SJudgeInput implements SData<SBlob> {
	private final STestImpl test;
	private SBlob data;
	
	public SJudgeInput(STestImpl test) { this.test = test; }
	
	@Override public SBlob get() { return data; }
	@Override public boolean isEnabled() { return true; }
	@Override public boolean isValid() { return true; }
	@Override public void update() { data = test.getJudge(); }
	@Override public void set(SBlob data) throws SException {
		this.data = data;
		test.setJudge(data);
	}
}
