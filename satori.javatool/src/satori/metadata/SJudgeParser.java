package satori.metadata;

import java.io.InputStreamReader;
import java.io.Reader;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.xml.parsers.DocumentBuilderFactory;

import org.apache.commons.io.IOUtils;
import org.apache.commons.io.LineIterator;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

import satori.data.SBlob;
import satori.task.SResultTask;
import satori.task.STaskException;
import satori.task.STaskHandler;
import satori.type.SBlobType;
import satori.type.SSizeType;
import satori.type.STextType;
import satori.type.STimeType;
import satori.type.SType;

public class SJudgeParser {
	@SuppressWarnings("serial")
	private static class ParseException extends Exception {
		public ParseException(String message) { super(message); }
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
		if (def_value != null && type == SBlobType.INSTANCE) throw new ParseException("Default value for blob inputs not supported");
		return new SInputMetadata(name, desc, type, required.equals("true"), def_value);
	}
	
	private static SOutputMetadata parseOutputParam(Element node) throws ParseException {
		String type_str = node.getAttribute("type");
		if (type_str.isEmpty()) throw new ParseException("Output type undefined");
		SType type;
		if (type_str.equals("text")) type = STextType.INSTANCE;
		else if (type_str.equals("time")) type = STimeType.INSTANCE;
		else if (type_str.equals("size")) type = SSizeType.INSTANCE;
		else if (type_str.equals("blob")) type = SBlobType.INSTANCE;
		else throw new ParseException("Unsupported output type: " + type_str);
		String name = node.getAttribute("name");
		if (name.isEmpty()) throw new ParseException("Output name undefined");
		String desc = node.getAttribute("description");
		if (desc.isEmpty()) throw new ParseException("Output description undefined");
		return new SOutputMetadata(name, desc, type);
	}
	
	private static List<SInputMetadata> parseInputs(Element node) throws ParseException {
		List<SInputMetadata> result = new ArrayList<SInputMetadata>();
		NodeList children = node.getElementsByTagName("param");
		for (int i = 0; i < children.getLength(); ++i) result.add(parseInputParam((Element)children.item(i)));
		return Collections.unmodifiableList(result);
	}
	private static void verifyInputs(List<SInputMetadata> inputs) throws ParseException {
		Set<String> names = new HashSet<String>();
		for (SInputMetadata input : inputs) {
			if (input.getName().equals("judge")) throw new ParseException("Illegal input name: judge");
			if (names.contains(input.getName())) throw new ParseException("Duplicate input name: " + input.getName());
			names.add(input.getName());
		}
	}
	
	private static List<SOutputMetadata> parseOutputs(Element node) throws ParseException {
		List<SOutputMetadata> result = new ArrayList<SOutputMetadata>();
		NodeList children = node.getElementsByTagName("param");
		for (int i = 0; i < children.getLength(); ++i) result.add(parseOutputParam((Element)children.item(i)));
		return Collections.unmodifiableList(result);
	}
	private static void verifyOutputs(List<SOutputMetadata> outputs) throws ParseException {
		Set<String> names = new HashSet<String>();
		for (SOutputMetadata output : outputs) {
			if (names.contains(output.getName())) throw new ParseException("Duplicate output name: " + output.getName());
			names.add(output.getName());
		}
	}
	
	private static void parse(Document doc, SJudge judge) throws ParseException {
		doc.normalizeDocument();
		Element node = doc.getDocumentElement();
		judge.setName(node.getAttribute("name"));
		NodeList input_children = node.getElementsByTagName("input");
		List<SInputMetadata> input_meta;
		if (input_children.getLength() == 0) input_meta = Collections.emptyList();
		else if (input_children.getLength() == 1) input_meta = parseInputs((Element)input_children.item(0));
		else throw new ParseException("Too many input groups");
		verifyInputs(input_meta);
		NodeList output_children = node.getElementsByTagName("output");
		judge.setInputMetadata(input_meta);
		List<SOutputMetadata> output_meta;
		if (output_children.getLength() == 0) output_meta = Collections.emptyList();
		else if (output_children.getLength() == 1) output_meta = parseOutputs((Element)output_children.item(0));
		else throw new ParseException("Too many output groups");
		verifyOutputs(output_meta);
		judge.setOutputMetadata(output_meta);
	}
	private static void parse(String str, SJudge judge) throws Exception {
		InputSource is = new InputSource();
		is.setCharacterStream(new StringReader(str));
		parse(DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(is), judge);
	}
	private static void parse(Reader reader, SJudge judge) throws Exception {
		StringBuilder xml = new StringBuilder();
		LineIterator line_iter = new LineIterator(reader);
		while (line_iter.hasNext()) {
			String line = line_iter.next();
			if (line.startsWith("#@")) xml.append(line.substring(2));
		}
		parse(xml.toString(), judge);
	}
	
	private static SJudge parseJudgeAux(STaskHandler handler, SBlob judge) throws Exception {
		SJudge result = new SJudge();
		result.setBlob(judge);
		handler.log(judge.getFile() != null ? "Parsing local judge file..." : "Loading and parsing judge blob...");
		Reader reader = new InputStreamReader(judge.getStreamTask());
		try { parse(reader, result); }
		finally { IOUtils.closeQuietly(reader); }
		return result;
	}
	
	private static Map<SBlob, SJudge> judges = new HashMap<SBlob, SJudge>();
	
	public static SJudge parseJudgeTask(STaskHandler handler, SBlob judge) throws Exception {
		if (judges.containsKey(judge)) return judges.get(judge);
		SJudge result = parseJudgeAux(handler, judge);
		judges.put(judge, result);
		return result;
	}
	public static SJudge parseJudge(final STaskHandler handler, final SBlob judge) throws STaskException {
		if (judges.containsKey(judge)) return judges.get(judge);
		SJudge result = handler.execute(new SResultTask<SJudge>() {
			@Override public SJudge run() throws Exception { return parseJudgeAux(handler, judge); }
		});
		judges.put(judge, result);
		return result;
	}
}
