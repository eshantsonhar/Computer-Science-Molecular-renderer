import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

import uk.ac.cam.ch.wwmm.opsin.NameToStructure;
import uk.ac.cam.ch.wwmm.opsin.NameToStructureConfig;
import uk.ac.cam.ch.wwmm.opsin.OpsinResult;

public final class OpsinBridge {
    private static String encode(String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(
                new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String name = reader.readLine();
        if (name == null) {
            throw new IllegalArgumentException("Expected one chemical name on standard input.");
        }

        OpsinResult result = NameToStructure.getInstance().parseChemicalName(
                name, NameToStructureConfig.getDefaultConfigInstance());
        String smiles = result.getSmiles();
        System.out.println(
                result.getStatus().name() + "\t"
                        + encode(smiles == null ? "" : smiles) + "\t"
                        + encode(result.getMessage() == null ? "" : result.getMessage()));
    }
}
