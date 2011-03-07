package satori.metadata;

import java.io.File;
import java.io.IOException;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

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
	private static void parse(String str, SJudge judge) throws ParseException {
		InputSource is = new InputSource();
		is.setCharacterStream(new StringReader(str));
		try { parse(DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(is), judge); }
		catch(IOException ex) { throw new ParseException(ex); }
		catch(SAXException ex) { throw new ParseException(ex); }
		catch(ParserConfigurationException ex) { throw new ParseException(ex); }
	}
	private static void parse(File file, SJudge judge) throws ParseException {
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
		parse(xml.toString(), judge);
	}
	
	private static Map<String, SJudge> judges = new HashMap<String, SJudge>();
	
	public static SJudge parseJudge(SBlob judge) throws SException {
		if (judges.containsKey(judge.getHash())) return judges.get(judge.getHash());
		File file = judge.getFile();
		boolean delete = false;
		if (file == null) {
			try { file = File.createTempFile("judge", null); }
			catch(IOException ex) { throw new SException(ex); }
			judge.saveLocal(file);
			delete = true;
		}
		SJudge result = new SJudge();
		result.setBlob(judge);
		parse(file, result);
		if (delete) file.delete();
		judges.put(judge.getHash(), result);
		return result;
	}
}
