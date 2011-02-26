package satori.metadata;

import java.io.File;
import java.io.IOException;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.LineIterator;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

import satori.blob.SBlob;
import satori.common.SException;
import satori.type.SBlobType;
import satori.type.SSizeType;
import satori.type.STextType;
import satori.type.STimeType;
import satori.type.SType;

public class SJudgeParser {
	@SuppressWarnings("serial")
	public static class ParseException extends SException {
		ParseException(String msg) { super(msg); }
		ParseException(Exception ex) { super(ex); }
	}
	
	public static class Result {
		private final List<SInputMetadata> input_meta;
		private final List<SOutputMetadata> output_meta;
		public Result(List<SInputMetadata> input_meta, List<SOutputMetadata> output_meta) {
			this.input_meta = input_meta;
			this.output_meta = output_meta;
		}
		public List<SInputMetadata> getInputMetadata() { return input_meta; }
		public List<SOutputMetadata> getOutputMetadata() { return output_meta; }
	}
	
	private static SInputMetadata parseInputParam(Element node) throws ParseException {
		String type_str = node.getAttribute("type");
		if (type_str.isEmpty()) throw new ParseException("Input type undefined");
		SType type;
		if (type_str.equals("text")) type = STextType.INSTANCE;
		else if (type_str.equals("time")) type = STimeType.INSTANCE;
		else if (type_str.equals("size")) type = SSizeType.INSTANCE;
		else if (type_str.equals("blob")) type = SBlobType.INSTANCE;
		else throw new ParseException("Unsupported input type: " + type_str);
		String name = node.getAttribute("name");
		if (name.isEmpty()) throw new ParseException("Input name undefined");
		String desc = node.getAttribute("description");
		if (desc.isEmpty()) throw new ParseException("Input description undefined");
		String required = node.getAttribute("required");
		if (required.isEmpty()) throw new ParseException("Input required mode undefined");
		if (!required.equals("true") && !required.equals("false")) throw new ParseException("Invalid input required mode: " + required); 
		String def_value = node.getAttribute("default");
		if (def_value.isEmpty()) def_value = null;
		return new SInputMetadata(name, desc, type, required.equals("true"), def_value); 
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
	
	private static List<SInputMetadata> parseInputs(Element node) throws ParseException {
		List<SInputMetadata> result = new ArrayList<SInputMetadata>();
		NodeList children = node.getElementsByTagName("param");
		for (int i = 0; i < children.getLength(); ++i) result.add(parseInputParam((Element)children.item(i)));
		return Collections.unmodifiableList(result);
	}
	
	private static Result parse(Document doc) throws ParseException {
		doc.normalizeDocument();
		Element node = doc.getDocumentElement();
		NodeList input_children = node.getElementsByTagName("input");
		if (input_children.getLength() != 1) throw new ParseException("Incorrect number of input groups");
		List<SInputMetadata> input_meta = parseInputs((Element)input_children.item(0));
		return new Result(input_meta, null);
	}
	private static Result parse(String str) throws ParseException {
		InputSource is = new InputSource();
		is.setCharacterStream(new StringReader(str));
		try { return parse(DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(is)); }
		catch(IOException ex) { throw new ParseException(ex); }
		catch(SAXException ex) { throw new ParseException(ex); }
		catch(ParserConfigurationException ex) { throw new ParseException(ex); }
	}
	private static Result parse(File file) throws ParseException {
		StringBuilder xml = new StringBuilder();
		LineIterator line_iter = null;
		try {
			line_iter = FileUtils.lineIterator(file);
			while (line_iter.hasNext()) {
				String line = line_iter.next();
				if (line.startsWith("#@")) xml.append(line.substring(2));
			}
		}
		catch(IOException ex) { throw new ParseException(ex); }
		finally { LineIterator.closeQuietly(line_iter); }
		return parse(xml.toString());
	}
	
	private static Map<String, Result> meta = new HashMap<String, Result>();
	
	public static Result parseJudge(SBlob judge) throws SException {
		if (meta.containsKey(judge.getHash())) return meta.get(judge.getHash());
		File file = judge.getFile();
		boolean delete = false;
		if (file == null) {
			try { file = File.createTempFile("judge", null); }
			catch(IOException ex) { throw new SException(ex); }
			judge.saveLocal(file);
			delete = true;
		}
		Result result = SJudgeParser.parse(file);
		if (delete) file.delete();
		meta.put(judge.getHash(), result);
		return result;
	}
}
