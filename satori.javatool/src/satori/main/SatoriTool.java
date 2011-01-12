package satori.main;

import javax.swing.*;


public class SatoriTool {
	private static final String xml =
		"<test>" +
		"  <stage name=\"stage\" description=\"Main stage\" default_enabled=\"true\">" +
		"    <input name=\"input\" description=\"Input file\" type=\"file\" required=\"true\" />" +
		"    <input name=\"hint\" description=\"Output/hint file\" type=\"file\" required=\"true\" />" +
		"    <input name=\"time\" description=\"Time limit\" type=\"value\" required=\"true\" default_value=\"1000\" />" +
		"    <input name=\"memory\" description=\"Memory limit\" type=\"value\" required=\"true\" default_value=\"67108864\" />" +
		"    <input name=\"checker\" description=\"Checker\" type=\"file\" required=\"false\" />" +
		"  </stage>" +
		"</test>";
	
	private static void start() {
		/*Problem.Iface problem_iface = new Problem.Client(ThriftClient.getProtocol());
		ProblemStruct struct = new ProblemStruct();
		struct.setName("Test");
		struct.setDescription("Testing problem");
		try { problem_iface.Problem_create(token, struct); }
		catch(TException ex) { MainFrame.showErrorDialog(new SatoriException(ex)); }*/
		
		/*TestCaseMetadata tc_meta;
		try { tc_meta = XmlParser.parse(xml); }
		catch(XmlParser.ParseException ex) { throw new RuntimeException(ex); }
		
		TestCase tc = tc_meta.createTestCase();
		tc.loadDefault();
		TestCaseContext context = tc.createContext();
		tc.update();
		
		TestPaneView pane = tc_meta.createTestPaneView();
		ColumnView column = new ColumnView();
		pane.addColumn(column);
		column.resetContext(context);*/
		
		SFrame frame = SFrame.get();
		/*ScrollPane scroll_pane = new ScrollPane();
		scroll_pane.setView(pane.getPane());
		frame.addPane("Test", scroll_pane);*/
		
		frame.start();
	}
	
	public static void main(String[] args) {
		SwingUtilities.invokeLater(new Runnable() {
			@Override public void run() { start(); }
		});
	}
}
