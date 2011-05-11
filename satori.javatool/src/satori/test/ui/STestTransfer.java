package satori.test.ui;

import java.awt.datatransfer.DataFlavor;

import satori.test.impl.STestImpl;
import satori.test.impl.STestSuiteBase;

public class STestTransfer {
	public static DataFlavor flavor = new DataFlavor(STestTransfer.class, "Satori test");
	
	private STestImpl test;
	private STestSuiteBase suite;
	
	public STestTransfer(STestImpl test, STestSuiteBase suite) {
		this.test = test;
		this.suite = suite;
	}
	
	public STestImpl getTest() { return test; }
	public STestSuiteBase getTestSuite() { return suite; }
}
