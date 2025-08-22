import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONObject;

public class SignatureCaptureIntegrator {
    public static void main(String[] args) {
        String pythonPath = "python";
        String wrapperScript = "capture_wrapper.py";
        String port = "COM8";
        int baudRate = 115200;
        String saveFolder = "firmas";
        boolean interactive = true;
        int defaultWidth = 100;
        int defaultHeight = 100;

        List<String> command = new ArrayList<>();
        command.add(pythonPath);
        command.add(wrapperScript);
        command.add("--port");
        command.add(port);
        command.add("--baud_rate");
        command.add(String.valueOf(baudRate));
        command.add("--save_folder");
        command.add(saveFolder);
        command.add("--interactive");
        command.add(String.valueOf(interactive));
        command.add("--default_width");
        command.add(String.valueOf(defaultWidth));
        command.add("--default_height");
        command.add(String.valueOf(defaultHeight));

        try {
            ProcessBuilder pb = new ProcessBuilder(command);
            Process process = pb.start();

            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            StringBuilder output = new StringBuilder();
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
                output.append(line);
            }

            BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()));
            while ((line = errorReader.readLine()) != null) {
                System.err.println("Error from Python: " + line);
            }

            int exitCode = process.waitFor();
            System.out.println("Proceso Python finalizado con código: " + exitCode);

            String jsonOutput = output.toString().trim().split("\n")[output.toString().trim().split("\n").length - 1];
            JSONObject result = new JSONObject(jsonOutput);
            if ("success".equals(result.getString("status"))) {
                System.out.println("Firma capturada exitosamente: " + result.getString("message"));
            } else {
                System.err.println("Error en captura: " + result.getString("message"));
            }

        } catch (Exception e) {
            System.err.println("Error al ejecutar Python desde Java: " + e.getMessage());
        }
    }
}