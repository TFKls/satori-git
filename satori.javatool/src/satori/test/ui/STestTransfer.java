package satori.test.ui;

import java.awt.datatransfer.DataFlavor;

import satori.problem.impl.STestSuiteImpl;
import satori.test.impl.STestImpl;

public class STestTransfer {
	public static DataFlavor flavor = new DataFlavor(STestTransfer.class, "Satori test");
	
	private STestImpl test;
	private STestSuiteImpl suite;
	
	public STestTransfer(STestImpl test, STestSuiteImpl suite) {
		this.test = test;
		this.suite = suite;
	}
	
	public STestImpl getTest() { return test; }
	public STestSuiteImpl getTestSuite() { return suite; }
}
