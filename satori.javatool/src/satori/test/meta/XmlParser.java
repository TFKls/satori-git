package satori.test.meta;

import java.io.IOException;
import java.io.StringReader;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

import satori.blob.SBlob;
import satori.common.SException;

public class XmlParser {
	@SuppressWarnings("serial")
	public static class ParseException extends SException {
		ParseException(String msg) { super(msg); }
		ParseException(Exception ex) { super(ex); }
	}
	
	private static InputMetadata parseInputValue(Element node) throws ParseException {
		String name = node.getAttribute("name");
		if (name.isEmpty()) throw new ParseException("Input name undefined");
		String desc = node.getAttribute("description");
		if (desc.isEmpty()) throw new ParseException("Input description undefined");
		String required = node.getAttribute("required");
		if (required.isEmpty()) throw new ParseException("Input required mode undefined");
		if (!required.equals("true") && !required.equals("false")) throw new ParseException("Invalid input required mode: " + required); 
		String def_value = node.getAttribute("default");
		if (def_value.isEmpty()) def_value = null;
		return new SStringInputMetadata(name, desc, required.equals("true"), def_value); 
	}
	
	private static InputMetadata parseInputFile(Element node) throws ParseException {
		String name = node.getAttribute("name");
		if (name.isEmpty()) throw new ParseException("Input name undefined");
		String desc = node.getAttribute("description");
		if (desc.isEmpty()) throw new ParseException("Input description undefined");
		String required = node.getAttribute("required");
		if (required.isEmpty()) throw new ParseException("Input required mode undefined");
		if (!required.equals("true") && !required.equals("false")) throw new ParseException("Invalid input required mode: " + required); 
		SBlob def_value = null;
		return new SBlobInputMetadata(name, desc, required.equals("true"), def_value);
	}
	
	/*private static OutputMetadata parseOutput(Element node) throws ParseException {
		String name = node.getAttribute("name");
		if (name.isEmpty()) throw new ParseException("Output name undefined");
		String desc = node.getAttribute("description");
		if (desc.isEmpty()) throw new ParseException("Output description undefined");
		String ret_mode = node.getAttribute("return");
		if (ret_mode.isEmpty()) throw new ParseException("Output return mode undefined");
		boolean ret_on_success = ret_mode.equals("always") || ret_mode.equals("success");
		boolean ret_on_failure = ret_mode.equals("always") || ret_mode.equals("failure");
		if (!ret_on_success && !ret_on_failure) throw new ParseException("Invalid output return mode: " + ret_mode);
		String requested = node.getAttribute("default_requested");
		if (requested.isEmpty()) throw new ParseException("Output default requested mode undefined");
		if (!requested.equalsIgnoreCase("true") && !requested.equalsIgnoreCase("false")) throw new ParseException("Invalid output default requested mode: " + requested); 
		String type = node.getAttribute("type");
		if (type.isEmpty()) throw new ParseException("Input type undefined");
		OutputMetadata meta;
		if (type.equals("value")) meta = new ValueOutputMetadata(name, desc, ret_on_success, ret_on_failure, requested.equals("true"));  
		else if (type.equals("file")) throw new ParseException("Output files not supported yet");
		else throw new ParseException("Invalid input type: " + type);
		return meta; 
	}*/
	
	/*private static StageMetadata parseStage(Element node) throws ParseException {
		String name = node.getAttribute("name");
		if (name.isEmpty()) throw new ParseException("Stage name undefined");
		String desc = node.getAttribute("description");
		if (desc.isEmpty()) throw new ParseException("Stage description undefined");
		String enabled = node.getAttribute("default_enabled");
		if (enabled.isEmpty()) throw new ParseException("Stage default enabled mode undefined");
		if (!enabled.equals("true") && !enabled.equals("false")) throw new ParseException("Invalid stage default enabled mode: " + enabled); 
		StageMetadata stage = new StageMetadata(name, desc, enabled.equals("true"));
		NodeList children = node.getElementsByTagName("*");
		for (int i = 0; i < children.getLength(); ++i) {
			Element child = (Element)children.item(i);
			if (child.getNodeName().equals("input")) stage.addInput(parseInput(child));
			else if (child.getNodeName().equals("output")) stage.addOutput(parseOutput(child));
			else throw new ParseException("Incorrect node: " + child.getNodeName());
		}
		return stage;
	}*/
	
	private static TestCaseMetadata parseInputs(Element node) throws ParseException {
		TestCaseMetadata testcase = new TestCaseMetadata();
		NodeList children = node.getElementsByTagName("*");
		for (int i = 0; i < children.getLength(); ++i) {
			Element child = (Element)children.item(i);
			if (child.getNodeName().equals("value")) testcase.addInput(parseInputValue(child));
			else if (child.getNodeName().equals("file")) testcase.addInput(parseInputFile(child));
			else throw new ParseException("Incorrect input type: " + child.getNodeName());
		}
		return testcase;
	}
	
	private static TestCaseMetadata parse(Document doc) throws ParseException {
		doc.normalizeDocument();
		Element node = doc.getDocumentElement();
		NodeList children = node.getElementsByTagName("input");
		if (children.getLength() != 1) throw new ParseException("Incorrect number of input groups");
		return parseInputs((Element)children.item(0));
	}
	
	public static TestCaseMetadata parse(String str) throws ParseException {
		InputSource is = new InputSource();
		is.setCharacterStream(new StringReader(str));
		try { return parse(DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(is)); }
		catch(IOException ex) { throw new RuntimeException(ex); }
		catch(SAXException ex) { throw new ParseException(ex); }
		catch(ParserConfigurationException ex) { throw new ParseException(ex); }
	}
}
