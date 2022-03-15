const loggerData = () => {
    const rawData = document.body.innerText.split('\n');
    console.log('r', rawData, 'l', rawData.length);
}

const extractWith = (rawData, pattern, indexTarget) => {
    let result;
    let patternIndex;
    rawData.some((value, index) => {
        if (value === pattern) {
            result = rawData[index + indexTarget]
            patternIndex = index
            return true;
        }
    });

    return { result, patternIndex };
}

const extractWithPattern = (rawData, pattern, indexTarget) => {
    const { result, patternIndex } = extractWith(rawData, pattern, indexTarget)
    return result;
}

const extractIndexWithPattern = (rawData, pattern) => {
    const { result, patternIndex } = extractWith(rawData, pattern, 0)
    return patternIndex;
}

const splitTextByPair = (rawData, currencyPair) => {
    operationClosePattern = "Depositar";
    bodyOpenPattern = currencyPair
    bodyClosePattern = "Orden"

    const operationsIndex = extractIndexWithPattern(rawData, operationClosePattern)
    let operationsText = rawData.slice();
    let remainingData = operationsText.splice(operationsIndex);
    const openIndex = extractIndexWithPattern(remainingData, bodyOpenPattern)
    remainingData= remainingData.splice (openIndex)
    const closeIndex = extractIndexWithPattern(remainingData, bodyClosePattern)
    let pairText = remainingData.slice(0, closeIndex)
    console.log(pairText)
    return { operationsText, pairText }
}

const getExtractors = (operationsText, currencyPair) => {

    let extract_rate = (pairText) => {
        const pattern = `online ${currencyPair}`;
        const indexTarget = -3;
        let result = extractWithPattern(pairText, pattern, indexTarget);
        result = parseInt(result.replace('%', ''));

        return result;
    };

    let extract_date = (pairText) => {
        const pattern = `online ${currencyPair}`;
        const indexTarget = 1;

        return extractWithPattern(pairText, pattern, indexTarget);
    };

    let extract_value = (pairText) => {
        const pattern = `Final de la`;
        const indexTarget = 2;

        return extractWithPattern(pairText, pattern, indexTarget);
    };

    let extract_remaining_time_operation = (operationsText) => { return null }; //

    let extract_deadline_interval = (pairText) => {
        const pattern = `Final de la`;
        const indexTarget = 4;

        return extractWithPattern(pairText, pattern, indexTarget);
    };

    operationsIndex = extractIndexWithPattern(operationsText, "Operaciones") - 1;
    const operations = parseInt(operationsText[operationsIndex]);
    //Tenemos al menos una operación activa
    if (operations >= 1) {
        extract_remaining_time_operation = () => {
            //const pairIndex = extractIndexWithPattern(operationsText, currencyPair)
            const pattern = currencyPair;
            const indexTarget = 5;

            return extractWithPattern(operationsText, pattern, indexTarget);
        };
    }

    return {
        extractor_rate: extract_rate, extractor_date: extract_date,
        extractor_value: extract_value, extractor_remaining_time_operation: extract_remaining_time_operation,
        extractor_deadline_interval: extract_deadline_interval
    };

}

const extractData = (rawData, currencyPair) => {

    //const rawData = document.body.innerText.split('\n');
    //currencyPair = "Basic Altcoin Index";
    let { operationsText, pairText } = splitTextByPair(rawData, currencyPair);

    const { extractor_rate, extractor_date, extractor_value,
        extractor_remaining_time_operation,
        extractor_deadline_interval } = getExtractors(operationsText, currencyPair);

    const rate = extractor_rate(pairText);
    const date = extractor_date(pairText);
    const value = extractor_value(pairText);
    const deadline_interval = extractor_deadline_interval(pairText);

    const remaining_time_operation = extractor_remaining_time_operation();

    const data = {
        rate: rate, date: date, value: value,
        remaining_time_operation: remaining_time_operation,
        deadline_interval: deadline_interval
    };

    return data;
}

const sendData = (rawData, currencyPair) => {

    const getDataPromise = new Promise((resolve, reject) => {
        data = extractData(rawData, currencyPair)
        let extraction = true; // we need a fail condition for the data extraction

        if (extraction) {
            resolve(data);
        } else {
            reject('Something is wrong my perro');
        }
    });

    getDataPromise.then((message) => {
        console.log("Currency pair:", currencyPair)
        console.log("promise is working...look at")
        console.log("Sending data: ", message);
        // Enviar a al server

    }).catch((message) => {
        console.log(message);
    });
}

//------------------------------ main -----------------------------------
let rawData = document.body.innerText.split('\n');
let currencyPair1 = "Gold";
let currencyPair2 = "USD CAD";

sendData(rawData,currencyPair1)
sendData(rawData,currencyPair2)


//const id = window.setInterval(extractData, 5000);
// window.clearInterval(id);